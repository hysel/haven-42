# Performance Review Fixture

## Purpose

Use this sanitized fixture to test the performance review workflow with realistic API, database, and async concerns.

## Input

Repository: `sample-order-service`
Service Type: ASP.NET Core API
Data Store: PostgreSQL
Expected Traffic: Moderate read-heavy API traffic

Relevant Change:

- Added a dashboard endpoint that returns recent orders with customer and line-item details.

Representative Code Context:

```csharp
[HttpGet("dashboard/recent-orders")]
public async Task<IReadOnlyList<OrderDashboardItem>> GetRecentOrders()
{
    var orders = await _db.Orders
        .OrderByDescending(order => order.CreatedAt)
        .Take(100)
        .ToListAsync();

    var result = new List<OrderDashboardItem>();

    foreach (var order in orders)
    {
        var customer = await _db.Customers.FirstAsync(customer => customer.Id == order.CustomerId);
        var lines = await _db.OrderLines.Where(line => line.OrderId == order.Id).ToListAsync();

        result.Add(OrderDashboardItem.From(order, customer, lines));
    }

    return result;
}
```

Known Concerns:

- Possible N+1 database queries for customers and order lines.
- No cancellation token is shown.
- No explicit projection is used.
- The endpoint returns a fixed 100 records but may still load more columns than needed.
- No caching or pagination decision is documented.

Expected Review Behavior:

- Identify N+1 queries as the primary performance risk.
- Recommend projection or eager loading shaped to the response.
- Recommend `AsNoTracking` for read-only queries where appropriate.
- Recommend cancellation token propagation.
- Ask about indexes on `Orders.CreatedAt`, `Customers.Id`, and `OrderLines.OrderId`.
- Avoid recommending caching before query shape and indexing are addressed.
