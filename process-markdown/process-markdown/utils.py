import asyncio

async def run_concurrently(tasks):
    """
    Runs a list of asyncio tasks concurrently and returns their results.
    Handles exceptions for individual tasks.
    """
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"A concurrent task failed: {result}")
        else:
            successful_results.append(result)
    return successful_results

if __name__ == "__main__":
    # Example usage:
    async def dummy_task(name, delay):
        print(f"Task {name}: Starting...")
        await asyncio.sleep(delay)
        print(f"Task {name}: Finished.")
        return f"Result from {name}"

    async def main_test():
        tasks_to_run = [
            dummy_task("A", 2),
            dummy_task("B", 1),
            dummy_task("C", 3)
        ]
        print("Running dummy tasks concurrently...")
        results = await run_concurrently([asyncio.create_task(task) for task in tasks_to_run])
        print("\nAll concurrent tasks completed. Results:")
        for res in results:
            print(res)

        # Example with an exception
        async def failing_task():
            await asyncio.sleep(0.5)
            raise ValueError("This task failed!")

        print("\nRunning tasks with a failing one...")
        results_with_failure = await run_concurrently([
            asyncio.create_task(dummy_task("D", 1)),
            asyncio.create_task(failing_task()),
            asyncio.create_task(dummy_task("E", 0.5))
        ])
        print("\nConcurrent tasks with failure completed. Results:")
        for res in results_with_failure:
            print(res)

    asyncio.run(main_test())