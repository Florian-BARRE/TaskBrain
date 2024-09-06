import asyncio

from brain import Brain
from logger import Logger, LogLevels


class MainBrain(Brain):
    def __init__(self, logger: Logger, share_attr1: int, share_attr2: int) -> None:
        super().__init__(logger, self)

        self.local_attr1: int = 0
        self.local_attr2: int = 0

    """ 
        MainProcess (mp) Tasks 
    """

    """ One-Shot Tasks """

    @Brain.task(process=False, run_on_start=True)
    async def mp_start(self):
        self.logger.log("[MP] MainBrain started", LogLevels.INFO)
        public_attributes = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        self.logger.log(f"[MP] Public attributes: {public_attributes}", LogLevels.INFO)

    """ Routine Tasks """

    @Brain.task(process=False, run_on_start=True, refresh_rate=1)
    async def mp_states_display(self):
        attributes_public = {k: v for k, v in self.__dict__.items() if
                             not k.startswith('_') and k.__str__() != "logger"}
        self.logger.log(f"[MP] Attributes states: {attributes_public}", LogLevels.INFO)

    @Brain.task(process=False, run_on_start=True, refresh_rate=1)
    async def mp_incrementer(self):
        self.share_attr1 += 1
        self.local_attr1 += 1

    @Brain.task(process=False, run_on_start=True, refresh_rate=1, timeout=5)
    async def mp_incrementer_with_timeout(self):
        self.share_attr1 += 10
        self.local_attr1 += 10

    """ 
        SubProcess (sb) Tasks 
        # Need to be synchronous function !
    """

    """ One-Shot Tasks """

    @Brain.task(process=True, run_on_start=True)
    def sb_start(self):
        self.logger.log("[SP] MainBrain started in another process", LogLevels.INFO)
        # In the other process we only have access to public attributes define after super().__init__()
        shared_attributes = {
            "share_attr1": self.share_attr1,
            "share_attr2": self.share_attr2
        }
        self.logger.log(f"[SP] Public attributes available in this subprocess: {shared_attributes}", LogLevels.INFO)

    """ Routine Tasks """

    @Brain.task(process=True, run_on_start=True, refresh_rate=1)
    def sp_states_display(self):
        shared_attributes = {
            "share_attr1": self.share_attr1,
            "share_attr2": self.share_attr2
        }
        self.logger.log(f"[SP] Attributes states: {shared_attributes}", LogLevels.INFO)

    @Brain.task(process=True, run_on_start=True, refresh_rate=1)
    def sb_incrementer(self):
        self.share_attr2 += 1
        # self.local_attr2 += 1 can't have access, define after super().__init__()

    @Brain.task(process=True, run_on_start=True, refresh_rate=1, timeout=5)
    def sb_incrementer_with_timeout(self):
        self.share_attr2 += 10

    @Brain.task(process=True, run_on_start=True, refresh_rate=1, define_loop_later=True,
                start_loop_marker="# ---Loop--- #")
    def sb_routine_with_setup(self):
        # In case of a subprocess routine need to use a no-serializable attribute
        # we can define it directly in the task then precise when loop have to start
        sb_non_serializable_attribute = "I'm not serializable attribute"

        # Call the loop start marker
        # ---Loop--- #
        self.logger.log(f"[SP] Non-serializable attribute: {sb_non_serializable_attribute}", LogLevels.INFO)

    """ Call others tasks """

    # Some function definition
    @Brain.task(process=False, run_on_start=False)
    async def callable_function_1(self):
        self.logger.log("[MP] Callable function 1", LogLevels.INFO)
        return 1

    @Brain.task(process=True, run_on_start=False)
    def callable_function_2(self):
        self.logger.log("[SP] Callable function 2", LogLevels.INFO)
        return 2

    # Call the tasks
    @Brain.task(process=False, run_on_start=True)
    async def call_tasks(self):
        await asyncio.sleep(10)  # Wait timed task to finish
        self.logger.log("[MP] Call tasks", LogLevels.INFO)
        f1_result = await self.callable_function_1()
        f2_result = await self.callable_function_2()  # Call the subprocess synchronous function as async one

        self.logger.log(f"[MP] Callable function 1 result: {f1_result.result}", LogLevels.INFO)
        # Can't get result because the function run in another process
        self.logger.log(f"[MP] Callable function 2 result: {f2_result.result}", LogLevels.INFO)
