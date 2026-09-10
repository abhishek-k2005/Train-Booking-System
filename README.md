# Train Booking System

A multithreaded train reservation backend simulating concurrent booking, cancellation and inquiry operations across 100 trains.

## Concepts Used
- Per-resource mutex isolation (`threading.Lock`) — fine-grained locking per train
- Counting semaphore (`threading.Semaphore`) — global concurrency threshold of 5
- Condition-variable-style wait/notify via semaphore acquire/release
- Time-bounded thread lifecycle management
- RAII-equivalent context manager scoping (`with` statement)

## File Structure
```
train_booking/
├── main.py       # Entry point — thread logic, operations, final report
├── config.py     # All constants and system parameters
└── README.md     # Project overview
```

## How to Run
```bash
python main.py
```

## Configuration (config.py)
| Parameter | Default | Meaning |
|---|---|---|
| MAX_TRAINS | 100 | Total trains |
| CAPACITY | 500 | Seats per train |
| MAX_THREADS | 20 | Concurrent user threads |
| MAX_CONCURRENT_ACCESS | 5 | Global semaphore cap |
| MAX_TIME | 1 | Thread lifetime (minutes) |
