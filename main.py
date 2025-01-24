# ====== Standard Library Imports ======
import asyncio

# ====== Internal Project Imports ======
from mainbrain import MainBrain
from logger import Logger, LogLevels

# ====== Main Execution ======
if __name__ == "__main__":
    # Initialize the logger with specified logging levels and configurations.
    brain_logger = Logger(
        identifier="Brain",
        decorator_level=LogLevels.DEBUG,
        print_log_level=LogLevels.DEBUG,
        print_log=True,
        write_to_file=False
    )

    # Create the MainBrain instance with the initialized logger and shared attributes.
    brain = MainBrain(
        logger=brain_logger,
        share_attr1=0,
        share_attr2=0
    )

    # Define an asynchronous function to execute tasks.
    async def run_tasks():
        """
        Gathers and runs all tasks asynchronously from the MainBrain instance.

        Returns:
            list: A list of results from the executed tasks.
        """
        # Retrieve and initialize all tasks from the MainBrain instance.
        tasks = [task() for task in brain.get_tasks()]
        # Asynchronously gather and execute all tasks.
        return await asyncio.gather(*tasks)


    # Run the asynchronous tasks using asyncio's event loop.
    asyncio.run(run_tasks())
