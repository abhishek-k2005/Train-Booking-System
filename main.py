import threading
import random
import time

# --- CONFIGURATION ---
MAX_TRAINS = 100
CAPACITY = 500
BOOK_MIN = 5
BOOK_MAX = 10
MAX_THREADS = 20
MAX_CONCURRENT_ACCESS = 5
MAX_TIME = 1  # minutes

# --- GLOBAL SHARED RESOURCES ---

# 1. Per-train locks (fine-grained mutex isolation)
train_locks = [threading.Lock() for _ in range(MAX_TRAINS)]
available_seats = [CAPACITY] * MAX_TRAINS

# 2. Global load control (counting semaphore pattern)
access_semaphore = threading.Semaphore(MAX_CONCURRENT_ACCESS)

# 3. Output lock
print_lock = threading.Lock()


# --- HELPER FUNCTIONS ---

def get_random_train():
    return random.randint(0, MAX_TRAINS - 1)

def get_random_bookings():
    return random.randint(BOOK_MIN, BOOK_MAX)

def safe_print(msg):
    with print_lock:
        print(msg)


# --- WORKER THREAD ---

def worker_thread(thread_num):
    start = time.time()

    while True:
        time.sleep(random.uniform(0, 0.5))

        # Time-bounded lifecycle check
        elapsed = time.time() - start
        if elapsed >= MAX_TIME * 60:
            break

        train_num = get_random_train()
        op_type = random.randint(1, 3)  # 1=Inquiry, 2=Booking, 3=Cancellation

        # --- PHASE 1: GLOBAL LOAD CONTROL (Counting Semaphore) ---
        safe_print(f"Thread {thread_num}: WAITING for system access.")
        access_semaphore.acquire()
        safe_print(f"Thread {thread_num}: GAINED system access.")

        try:
            # --- PHASE 2: PER-TRAIN MUTEX ISOLATION ---
            with train_locks[train_num]:

                # --- PHASE 3: EXECUTE OPERATION ---
                if op_type == 1:  # Inquiry
                    with print_lock:
                        print(f"Thread {thread_num}: Train {train_num} "
                              f"has {available_seats[train_num]} seats available.")

                elif op_type == 2:  # Booking
                    num_to_book = get_random_bookings()
                    with print_lock:
                        if available_seats[train_num] >= num_to_book:
                            available_seats[train_num] -= num_to_book
                            print(f"Thread {thread_num}: SUCCESSFULLY BOOKED {num_to_book} "
                                  f"seats on Train {train_num}. "
                                  f"Remaining: {available_seats[train_num]}")
                        else:
                            print(f"Thread {thread_num}: FAILED to book on Train {train_num}. "
                                  f"Not enough seats.")

                elif op_type == 3:  # Cancellation
                    booked_seats = CAPACITY - available_seats[train_num]
                    with print_lock:
                        if booked_seats > 0:
                            num_to_cancel = random.randint(1, booked_seats)
                            available_seats[train_num] += num_to_cancel
                            print(f"Thread {thread_num}: SUCCESSFULLY CANCELLED {num_to_cancel} "
                                  f"seats on Train {train_num}. "
                                  f"Remaining: {available_seats[train_num]}")
                        else:
                            print(f"Thread {thread_num}: Train {train_num} "
                                  f"has no bookings to cancel.")

        finally:
            # --- PHASE 4: RELEASE GLOBAL ACCESS SLOT ---
            access_semaphore.release()


# --- MAIN ---

def main():
    print("--- Train Booking System Started ---\n")

    threads = []
    for i in range(MAX_THREADS):
        t = threading.Thread(target=worker_thread, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\n--- Final Reservation Chart ---")
    print(f"{'Train':>10}  {'Available Seats':>15}")
    for i in range(MAX_TRAINS):
        print(f"{i:>10}  {available_seats[i]:>15}")
    print("\nThanks for using our services!")


if __name__ == "__main__":
    main()