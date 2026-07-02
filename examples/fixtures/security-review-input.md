# Security Review Fixture

## Purpose

Use this sanitized fixture to test the security review workflow without exposing real application code or credentials.

## Input

Repository: `sample-order-service`
Service Type: ASP.NET Core API
Authentication: JWT bearer tokens
Authorization: Role-based policies
Data Store: PostgreSQL
Logging: Structured logging

Relevant Change:

- Added an endpoint for exporting customer order history.
- Added request logging around export attempts.
- Added a new repository query that filters by `customerId`.

Representative Code Context:

```csharp
[Authorize]
[HttpGet("customers/{customerId}/orders/export")]
public async Task<IActionResult> ExportOrders(string customerId)
{
    _logger.LogInformation("Export requested for {CustomerId} by {User}", customerId, User.Identity?.Name);

    var orders = await _orders.GetOrdersForCustomerAsync(customerId);
    return File(_exporter.ToCsv(orders), "text/csv", "orders.csv");
}
```

Known Concerns:

- The endpoint relies on authentication but does not show an ownership or authorization check.
- The route accepts `customerId` directly from the caller.
- Logs include a customer identifier and user name.
- Exported data may include sensitive customer order details.
- No rate limiting or audit event is shown.

Expected Review Behavior:

- Identify missing object-level authorization as the highest risk.
- Ask whether users may export only their own orders or orders for managed accounts.
- Recommend explicit authorization before querying or exporting data.
- Review logging for privacy and data minimization.
- Recommend tests for unauthorized access and cross-customer access.
- Avoid claiming SQL injection unless repository query details are provided.
