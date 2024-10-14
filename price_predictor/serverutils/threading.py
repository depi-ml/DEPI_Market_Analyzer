import os
import psutil

def get_optimal_worker_count():
    # Get the number of CPU cores
    cpu_count = os.cpu_count()

    # Get available memory
    available_memory = psutil.virtual_memory().available

    # Estimate memory per worker (adjust this based on your application's needs)
    estimated_memory_per_worker = 500 * 1024 * 1024  # 500 MB

    # Calculate workers based on CPU and memory
    cpu_based_workers = cpu_count * 2  # A common rule of thumb is 2-4 threads per CPU core
    memory_based_workers = available_memory // estimated_memory_per_worker

    # Choose the lower of the two to avoid overloading the system
    optimal_workers = min(cpu_based_workers, memory_based_workers)

    # Ensure we have at least 2 workers and no more than 32
    return max(2, min(optimal_workers, 32))