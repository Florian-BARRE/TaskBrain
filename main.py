import asyncio
from mainbrain import MainBrain
from logger import Logger, LogLevels

if __name__ == "__main__":
    brain_logger = Logger(
        identifier="Brain",
        decorator_level=LogLevels.DEBUG,
        print_log_level=LogLevels.DEBUG,
        print_log=True,
        write_to_file=False
    )

    brain = MainBrain(
        logger=brain_logger,
        share_attr1=0,
        share_attr2=0
    )

    # Start tasks
    async def run_tasks():
        tasks = [task() for task in brain.get_tasks()]
        return await asyncio.gather(*tasks)

    asyncio.run(run_tasks())
