# Design Decisions & Trade-offs

## 1. Relational Database (PostgreSQL) vs. In-Memory Queue (Redis/RabbitMQ)
- **Decision**: I chose to use PostgreSQL as the primary data store for Jobs and Queues, rather than a traditional message broker like RabbitMQ or pure Redis lists.
- **Trade-off**: While RabbitMQ/Redis are faster for raw throughput (millions of msgs/sec), using PostgreSQL gives me strict ACID guarantees, persistent state, complex querying (e.g., viewing a specific job's status via the dashboard), and relational data integrity (Users -> Organizations -> Projects -> Queues -> Jobs). I trade microsecond latency for durability, observability, and data integrity.
- **Implementation Detail**: To prevent workers from picking up the same job concurrently, I heavily rely on Postgres's `SELECT ... FOR UPDATE SKIP LOCKED` feature. This provides atomic, row-level locking that effectively turns a relational table into a highly concurrent queue.

## 2. FastAPI (Async) vs. Django/Flask (Sync)
- **Decision**: I chose FastAPI combined with `asyncpg`.
- **Trade-off**: The async nature of FastAPI allows the server to handle tens of thousands of concurrent connections (like job submissions or polling requests) on a single thread without blocking. This is crucial for a high-throughput scheduler. The trade-off is the added complexity of writing asynchronous Python (e.g., `await`, async session management) compared to Django's synchronous ORM.

## 3. Pull vs. Push Worker Architecture
- **Decision**: Workers *pull* (poll) for jobs from the database rather than having the API *push* jobs to them.
- **Trade-off**: A pull architecture makes it incredibly easy to scale workers horizontally. You simply spin up a new container, and it inherently starts pulling from the queues. A push architecture requires complex registry management and load balancing. The downside of pulling is potential database load from constant polling, which I mitigated by using exponential backoffs in the worker polling loop if queues are empty.

## 4. Polling for Metrics (Frontend) vs. WebSockets
- **Decision**: The React dashboard uses HTTP polling (`setInterval` for `fetch`) to retrieve system metrics every 2 seconds.
- **Trade-off**: WebSockets would provide true real-time, event-driven updates. However, for an administrative dashboard, a 2-second HTTP poll provides "near real-time" visibility while vastly simplifying the backend architecture (avoiding WebSocket connection management, ping/pong heartbeats, and pub/sub broadcasting). 

## 5. Idempotency
- **Decision**: Jobs support an `idempotency_key`.
- **Trade-off**: Distributed systems guarantee "at-least-once" delivery. If a worker crashes right after finishing a job but before updating the database, another worker might pick it up. Relying on an idempotency key ensures that the actual *execution* logic won't process the same data twice. This shifts some responsibility to the job payload itself but ensures system safety against network partitions.

## 6. Security & Authentication
- **Decision**: All API endpoints and dashboard metrics are secured using stateless JSON Web Tokens (JWTs).
- **Trade-off**: Using JWTs over stateful session cookies ensures the FastAPI backend remains entirely stateless. This means we can deploy the API behind a load balancer without worrying about sticky sessions. The trade-off is the inability to forcefully instantly revoke a token before its natural expiration, which we accept for this specific administrative use case.
