[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent (Resolve-Path -LiteralPath $Path))

$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path -LiteralPath $Path),
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    throw "PowerShell parser errors in ${Path}: $($errors -join '; ')"
}

function Get-VariableName {
    param([System.Management.Automation.Language.Ast]$Node)
    if ($Node -is [System.Management.Automation.Language.VariableExpressionAst]) {
        return $Node.VariablePath.UserPath
    }
    return $null
}

function Get-LoopValues {
    param(
        [System.Management.Automation.Language.Ast]$Node,
        [string]$VariableName
    )
    $cursor = $Node.Parent
    while ($null -ne $cursor) {
        if ($cursor -is [System.Management.Automation.Language.ForEachStatementAst] -and
            $cursor.Variable.VariablePath.UserPath -eq $VariableName) {
            $values = @()
            foreach ($match in [regex]::Matches($cursor.Condition.Extent.Text, '["'']([^"'']+)["'']')) {
                $values += $match.Groups[1].Value
            }
            return $values
        }
        $cursor = $cursor.Parent
    }
    return @()
}

function Get-Patterns {
    param([System.Management.Automation.Language.ExpressionAst]$Expression)

    if ($Expression -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
        return @($Expression.Value)
    }
    if ($Expression -is [System.Management.Automation.Language.ExpandableStringExpressionAst] -and
        $Expression.NestedExpressions.Count -eq 0) {
        return @($Expression.Value)
    }
    if ($Expression -is [System.Management.Automation.Language.VariableExpressionAst]) {
        return @(Get-LoopValues -Node $Expression -VariableName $Expression.VariablePath.UserPath)
    }
    if ($Expression -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and
        $Expression.Expression.Extent.Text -eq '[regex]' -and
        $Expression.Member.Value -eq 'Escape' -and
        $Expression.Arguments.Count -eq 1) {
        $argument = $Expression.Arguments[0]
        $rawValues = @()
        if ($argument -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
            $rawValues = @($argument.Value)
        }
        elseif ($argument -is [System.Management.Automation.Language.VariableExpressionAst]) {
            $rawValues = @(Get-LoopValues -Node $argument -VariableName $argument.VariablePath.UserPath)
        }
        return @($rawValues | ForEach-Object { [regex]::Escape($_) })
    }
    return @()
}

$results = New-Object System.Collections.Generic.List[object]
$tests = $ast.FindAll({
    param($node)
    $node -is [System.Management.Automation.Language.CommandAst] -and
        $node.GetCommandName() -eq 'Invoke-PackTest'
}, $true)

foreach ($test in $tests) {
    if ($test.CommandElements.Count -lt 3 -or
        $test.CommandElements[1] -isnot [System.Management.Automation.Language.StringConstantExpressionAst] -or
        $test.CommandElements[2] -isnot [System.Management.Automation.Language.ScriptBlockExpressionAst]) {
        continue
    }

    $testName = $test.CommandElements[1].Value
    $body = $test.CommandElements[2]
    $pathVariables = @{}
    $contentVariables = @{}

    $assignments = $body.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.AssignmentStatementAst]
    }, $true)

    foreach ($assignment in $assignments) {
        $leftName = Get-VariableName -Node $assignment.Left
        if ([string]::IsNullOrWhiteSpace($leftName)) {
            continue
        }
        $right = $assignment.Right.Extent.Text

        $pathMatch = [regex]::Match($right, 'Join-Path\s+\$repoRoot\s+["'']([^"'']+)["'']')
        if ($pathMatch.Success) {
            $pathVariables[$leftName] = $pathMatch.Groups[1].Value.Replace('\', '/')
            continue
        }

        $contentMatch = [regex]::Match(
            $right,
            '(?:Get-Content\b[^\r\n]*?-LiteralPath\s+|ReadAllText\()\$([A-Za-z_][A-Za-z0-9_]*)'
        )
        if ($contentMatch.Success -and $pathVariables.ContainsKey($contentMatch.Groups[1].Value)) {
            $contentVariables[$leftName] = $pathVariables[$contentMatch.Groups[1].Value]
        }
    }

    $matches = $body.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.BinaryExpressionAst] -and
            $node.Operator -in @(
                [System.Management.Automation.Language.TokenKind]::Imatch,
                [System.Management.Automation.Language.TokenKind]::Ilike
            )
    }, $true)

    foreach ($match in $matches) {
        $leftName = Get-VariableName -Node $match.Left
        if ([string]::IsNullOrWhiteSpace($leftName) -or -not $contentVariables.ContainsKey($leftName)) {
            continue
        }
        $patterns = @(Get-Patterns -Expression $match.Right)
        foreach ($pattern in $patterns) {
            $sourcePath = Join-Path $repoRoot $contentVariables[$leftName]
            $sourceText = if (Test-Path -LiteralPath $sourcePath) {
                [System.IO.File]::ReadAllText($sourcePath)
            }
            else {
                $null
            }
            $matchesSource = if ($match.Operator -eq [System.Management.Automation.Language.TokenKind]::Ilike) {
                $sourceText -like $pattern
            }
            else {
                $sourceText -match $pattern
            }
            if (-not [string]::IsNullOrWhiteSpace($pattern) -and
                $null -ne $sourceText -and
                $matchesSource) {
                $results.Add([pscustomobject]@{
                    source = $contentVariables[$leftName]
                    pattern = $pattern
                    test = "scripts/test-pack.ps1::$testName"
                    variable = "`$$leftName"
                    line = $match.Extent.StartLineNumber
                })
            }
        }
    }

    $containsCalls = $body.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and
            $node.Member.Value -eq 'Contains' -and
            $node.Arguments.Count -eq 1
    }, $true)
    foreach ($call in $containsCalls) {
        $leftName = Get-VariableName -Node $call.Expression
        if ([string]::IsNullOrWhiteSpace($leftName) -or -not $contentVariables.ContainsKey($leftName)) {
            continue
        }
        $patterns = @(Get-Patterns -Expression $call.Arguments[0])
        $sourcePath = Join-Path $repoRoot $contentVariables[$leftName]
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            continue
        }
        $sourceText = [System.IO.File]::ReadAllText($sourcePath)
        foreach ($pattern in $patterns) {
            if (-not [string]::IsNullOrWhiteSpace($pattern) -and $sourceText.Contains($pattern)) {
                $results.Add([pscustomobject]@{
                    source = $contentVariables[$leftName]
                    pattern = $pattern
                    test = "scripts/test-pack.ps1::$testName"
                    variable = "`$$leftName"
                    line = $call.Extent.StartLineNumber
                })
            }
        }
    }
}

$results | ConvertTo-Json -Depth 4
