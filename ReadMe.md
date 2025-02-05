# TaskBrain -- English Documentation

Using **TaskBrain** is highly recommended when your application requires executing multiple tasks in parallel across
different processes. This module heavily relies on Python's **Asyncio** library, allowing the management of asynchronous
code execution as well as multiprocessing.

## Advantages:

- **Error management**
- **Execution isolation**
- **Detailed logs of task executions**
- **All methods share class attributes via `self`, ensuring seamless intercommunication**

---

## Task

To transform a **Brain** method into a task and be able to control its execution as needed, simply use
the `Brain.task()` decorator.

```python
@Brain.task(...)
async def my_method(self):
   pass
```

This decorator includes **two mandatory parameters**: `process` and `run_on_start`. These have been made **mandatory**
to improve code clarity—this makes it clear **which methods execute in a secondary process and which ones start when the
Brain launches**.

Now, let's explore all the possible configurations of this decorator and the options it provides.

---

### **One-Shot**

For all tasks that only need to be executed **once**, we decorate the method to create a **"one_shot_task"**.

```python
@Brain.task(process=[True / False], run_on_start=[True / False])
async def one_shot_method(self):
   pass
```

---

### **Routine**

For tasks that need to run **continuously**, we can specify a `refresh_rate` in the decorator. This parameter defines *
*the execution frequency of the method**. It will then be called indefinitely (even if it crashes) with a pause
corresponding to the `refresh_rate` duration.

```python
@Brain.task(process=[True / False], run_on_start=[True / False], refresh_rate=0.5)
async def routine_method(self):
   pass
```

Here, this method will be executed **indefinitely** with a **0.5s pause** between each execution.

---

### **Timeout and Task**

A **timeout** can be added to both **routines and one_shot tasks**, meaning the task will be **interrupted after a set
duration**. This is particularly useful when defining precise execution phases.

This feature applies to both **routines** and **one-shot tasks**!

```python
# Timed Routine
@Brain.task(process=[True / False], run_on_start=[True / False], refresh_rate=[duration in seconds], timeout=10)
async def timed_routine_method(self):
   pass


# Timed One-Shot
@Brain.task(process=[True / False], run_on_start=[True / False], timeout=10)
async def timed_one_shot_method(self):
   pass
```

Here, both methods will **stop execution after 10 seconds**, no matter what.

---

## **Execution Output Management**

Once executed, methods return an **execution code** indicating **how the task finished**. The possible states are:

```python
class ExecutionStates(IntEnum):
   CORRECTLY = 0  # Normal execution: no timeout or crash
   TIMEOUT = 1  # Task stopped because it exceeded the timeout
   ERROR_OCCURRED = 2  # Task stopped due to an error (function crash)
```

---

## **Multiprocessing**

A **task (routine or one-shot)** can be executed in a **separate process** to better distribute CPU load. This feature
is particularly useful for **resource-intensive tasks** that might otherwise block the **main process**.

The **biggest challenge in multiprocessing** is **communication between Python objects across processes**. In *
*TaskBrain**, this communication is fully automated. When a **process is launched**, a **copy** of the **Brain's
attributes** is created and shared among all processes.

Whenever one of these attributes is **modified** (whether from `main_process → second_process`
or `second_process → main_process`), the **Brain automatically synchronizes** this change back to the **initial instance
**.

This **shared copy** is a **proxy dictionary**, a **special type from Python's `multiprocessing.Manager`** class.

---

## **Inter-Process Communication Limitations**

The **main limitation** when using this feature is **the type of class attributes** that can be shared through the *
*proxy dictionary**.

### **Supported serializable types**:

```python
serialized_types = (
   Logger,  # Logger from loggerplusplus library (serialized since V0.1.2)
   int,
   float,
   str,
   list,
   set,
   dict,
   tuple,
   type(None),
)
```

Complex objects **cannot** be shared **directly** between processes. To work around this, you can **instantiate** the
object **inside the process**.

---

## **Example: Using a Camera in Another Process**

Using a **camera** is **resource-intensive**, making it **ideal** for multiprocessing. However, **camera objects are not
serializable**!

So, instead of **sharing the object**, we **retrieve its configuration via attributes** and **instantiate it inside the
process**.

```python
@Brain.task(process=True, run_on_start=[True / False])
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )
```

> **⚠️ Important:** A **process is synchronous**! Use `def`, not `async def`.

---

## **Looping Inside a Process Task**

Once we **instantiate** our camera, we **use it to capture images and apply processing**. However, this introduces *
*another issue**:

- The **image processing** must **run continuously**.
- But we **cannot create a routine inside another task**—especially **inside a separate process**.

To solve this, we use the **`define_loop_later`** option. This allows defining **a task as a routine** while **also
executing a one-time setup part**.

```python
@Brain.task(process=True, run_on_start=[True / False], refresh_rate=0.1, define_loop_later=True)
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )

   # ---Loop--- #
   camera.capture()
   # ... image processing ... #
```

---

### **Manually Defining the Loop Marker**

A **custom marker** can be used to define where the routine starts:

```python
@Brain.task(process=True, run_on_start=[True / False], refresh_rate=0.1, define_loop_later=True,
            start_loop_marker="#- My Custom Loop Marker -#")
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )

   # - My Custom Loop Marker -#
   camera.capture()
   # ... image processing ... #
```

---

## **Vigilance Points, Limitations & Key Considerations**

Although using **TaskBrain** is powerful, there are **several key points** to watch for to get the best performance.

### **Dynamic Initialization**

#### **Automatic Attribute Creation**

To **simplify** the `__init__` method and avoid redundant code:

Instead of writing:

```python
def __init__(self, logger: Logger, obj1: type_obj1, obj2: type_obj2, obj3: type_obj3) -> None:
   self.logger = logger
   self.obj1 = obj1
   self.obj2 = obj2
   self.obj3 = obj3
```

Simply use:

```python
def __init__(self, logger: Logger, obj1: type_obj1, obj2: type_obj2, obj3: type_obj3) -> None:
   super().__init__(logger, self)
```

Here is the continuation of the **full English translation** while maintaining the original **markdown formatting**.

---

## **Class Attribute Creation**

If we want to create **class attributes** inside `__init__` and make them **accessible across multiple processes**, we
must **define them before** calling `super().__init__(logger, self)`.

Otherwise, they will **only be available in the main process**.

```python
def __init__(
        self,
        logger: Logger,
        obj1: type_obj1,
        obj2: type_obj2,
        obj3: type_obj3,
) -> None:
   # Attributes available in all processes
   self.attr_multi_process = 0

   super().__init__(logger, self)

   # Attributes available only in the main process
   self.attr_main_process = 0
```

---

## **Attribute Serialization**

When `__init__` is called, **TaskBrain automatically serializes all class attributes**.

However, **most objects are not serializable**. If an **attribute cannot be serialized**, a **warning message** will be
logged.

> **⚠️ This is a warning, not an error.**  
> Any **non-serialized attribute** will **not be available in other processes**.

**Example warning message:**

```
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_cmd].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_pami].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_lidar].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_odometer].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_camera].
```

---

## **Refresh Rate Limitations**

The execution of tasks relies on **asynchronous execution**, meaning **pseudo-parallelism**.

> **Key Consideration:**  
> A routine with a **very low `refresh_rate`** will **monopolize CPU time**, which can **slow down the entire Brain
execution**.

**Setting `refresh_rate` to `0` is prohibited!**  
This parameter **must be carefully adjusted** to optimize performance.

---

## **Inter-Process Communication Limitations**

As previously explained, **synchronization between the shared Brain and its instance** is done via a **high-frequency
routine**.

By default, its `refresh_rate` is set to **0.01 seconds**.

Although this method is **optimized for minimal execution time**, it **is not instantaneous**!  
This **must be considered** when deciding **to move a process to another task**.

---

## **Complete Usage Example**

Here is a **full example** of how to use the **TaskBrain module** inside a **main script**.

```python
import asyncio
from taskbrain import Brain
from loggerplusplus import Logger


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
      self.logger.info("[MP] MainBrain started")
      public_attributes = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
      self.logger.info(f"[MP] Public attributes: {public_attributes}")

   """ Routine Tasks """

   @Brain.task(process=False, run_on_start=True, refresh_rate=1)
   async def mp_states_display(self):
      attributes_public = {k: v for k, v in self.__dict__.items() if
                           not k.startswith('_') and k.__str__() != "logger"}
      self.logger.info(f"[MP] Attributes states: {attributes_public}")

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
   """

   """ One-Shot Tasks """

   @Brain.task(process=True, run_on_start=True)
   def sb_start(self):
      self.logger.info("[SP] MainBrain started in another process")
      shared_attributes = {
         "share_attr1": self.share_attr1,
         "share_attr2": self.share_attr2
      }
      self.logger.info(f"[SP] Public attributes available in this subprocess: {shared_attributes}")

   """ Routine Tasks """

   @Brain.task(process=True, run_on_start=True, refresh_rate=1)
   def sp_states_display(self):
      shared_attributes = {
         "share_attr1": self.share_attr1,
         "share_attr2": self.share_attr2
      }
      self.logger.info(f"[SP] Attributes states: {shared_attributes}")

   @Brain.task(process=True, run_on_start=True, refresh_rate=1)
   def sb_incrementer(self):
      self.share_attr2 += 1

   @Brain.task(process=True, run_on_start=True, refresh_rate=1, timeout=5)
   def sb_incrementer_with_timeout(self):
      self.share_attr2 += 10

   @Brain.task(process=True, run_on_start=True, refresh_rate=1, define_loop_later=True,
               start_loop_marker="# ---Loop--- #")
   def sb_routine_with_setup(self):
      sb_non_serializable_attribute = "I'm not serializable attribute"
      # ---Loop--- #
      self.logger.info(f"[SP] Non-serializable attribute: {sb_non_serializable_attribute}")

   """ Call other tasks """

   @Brain.task(process=False, run_on_start=False)
   async def callable_function_1(self):
      self.logger.info("[MP] Callable function 1")
      return 1

   @Brain.task(process=True, run_on_start=False)
   def callable_function_2(self):
      self.logger.info("[SP] Callable function 2")
      return 2

   @Brain.task(process=False, run_on_start=True)
   async def call_tasks(self):
      await asyncio.sleep(10)  # Wait for timed task to finish
      self.logger.info("[MP] Call tasks")
      f1_result = await self.callable_function_1()
      f2_result = await self.callable_function_2()

      self.logger.info(f"[MP] Callable function 1 result: {f1_result.result}")
      self.logger.info(f"[MP] Callable function 2 result: {f2_result.result}")
```

---

### **Usage in a Main Script**

Here’s how to **integrate and launch your Brain** inside a **main script**:

```python
import asyncio
from exemple.mainbrain import MainBrain
from loggerplusplus import Logger

if __name__ == "__main__":
   brain_logger = Logger(
      identifier="Brain",
      print_log=True,
      write_to_file=False,
      display_monitoring=False,
      files_monitoring=False,
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
```

---

### **Explanation of the Main Script**

1. **Initialize the Logger**: A logger is created with a **debug level** that prints logs to the
   console (`print_log=True`).
2. **Initialize the Brain**: `MainBrain` is initialized with **two shared attributes (`share_attr1` and `share_attr2`)**
   and the logger.
3. **Execute Tasks**:
   - **Retrieve all tasks** using `brain.get_tasks()`.
   - **Execute them asynchronously** using `asyncio.gather()`.

This script demonstrates **how to initialize and execute various Brain tasks**, including **async tasks, routines, and
multiprocessing**.

---

## **Author**

Project created and maintained by **Florian BARRE**.  
For questions or contributions, feel free to contact me.

[My Website](https://florianbarre.fr/) | [My LinkedIn](www.linkedin.com/in/barre-florian) | [My GitHub](https://github.com/Florian-BARRE)
---

---

# TaskBrain -- Documentation Française

L'utilisation de **taskbrain** est fortement conseillée lorsque votre application nécessite l'exécution de multiples
tâches, en parallèle, dans des processus différents. Ce module s'appuie largement sur la bibliothèque Asyncio de Python,
ce qui permet de gérer l'exécution de code asynchrone ainsi que le multiprocessing.

## Avantages :

- Gestion des erreurs
- Isolation des exécutions
- Journaux détaillés des exécutions des tâches
- Toutes les méthodes partagent les attributs de la classe via le self, assurant ainsi une intercommunication
  transparente

## Task

Pour transformer une méthode du Brain en tâche et ainsi pouvoir contrôler son exécution comme on veut, il suffit
d’utiliser le décorateur `Brain.task()`.

```python
@Brain.task(...)
async def ma_methode(self):
   pass
```

Ce décorateur comprend 2 paramètres obligatoires à compléter : `process` et `run_on_start`. Ils ont été rendus
obligatoires afin d’améliorer la clarté du code ; cela permet de bien voir quelle méthode s’exécute dans un processus
secondaire et quelles méthodes démarrent au lancement du Brain.

Nous allons à présent voir toutes les configurations possibles de ce décorateur et les possibilités qu’il offre.

### One-Shot

Pour toutes les tâches qui n’ont besoin d’être exécutées qu’une seule fois, on va décorer la méthode de sorte à créer ce
qu’on appelle une “one_shot_task”.

```python
@Brain.task(process=[True / False], run_on_start=[True / False])
async def methode_one_shot(self):
   pass
```

### Routine

Pour toutes les tâches qui s’exécutent à l’infini, il est possible de préciser à notre tâche, via le décorateur,
un `refresh_rate`. Ce paramètre correspond à la fréquence d’exécution de la méthode. Elle sera alors appelée à
l’infini (même si elle plante) avec une pause de la durée du `refresh_rate` renseigné.

```python
@Brain.task(process=[True / False], run_on_start=[True / False], refresh_rate=0.5)
async def methode_routine(self):
   pass
```

Ici, cette méthode sera donc exécutée à l’infini avec une pause de 0.5s entre chaque exécution.

### Timeout et Task

Il est possible d’ajouter à notre task (routine ou one_shot) un timeout au bout duquel la tâche sera interrompue. Cela
est utile notamment lorsqu’on définit des phases précises d'exécution.

Cette fonctionnalité est applicable aux routines et aux one_shot !

```python
# Routine timée
@Brain.task(process=[True / False], run_on_start=[True / False], refresh_rate=[durée en seconde], timeout=10)
async def methode_timed_routine(self):
   pass


# One_shot timée
@Brain.task(process=[True / False], run_on_start=[True / False], timeout=10)
async def methode_timed_one_shot(self):
   pass
```

Ici, ces deux méthodes s’interrompront quoi qu’il arrive au bout de 10 secondes.

> Gestion des outputs

Les méthodes, une fois exécutées, retournent un code d’exécution afin d’indiquer comment la tâche s’est terminée. Voici
les états possibles :

```python
class ExecutionStates(IntEnum):
   CORRECTLY = 0  # Exécution normale: pas de timeout ni de crash
   TIMEOUT = 1  # La task s'est interrompue car elle a dépassé le timeout
   ERROR_OCCURRED = 2  # La task s'est interrompue car une erreur est survenue (crash de la fonction)
```

### Multiprocessing

Il est possible d'exécuter une task (routine ou one_shot) dans un autre processus afin de mieux répartir la charge CPU.
Cette fonctionnalité est particulièrement utile pour les tâches gourmandes en ressources, qui pourraient autrement
bloquer excessivement le temps CPU du processus principal. La principale difficulté du multiprocessing réside dans la
communication d'objets Python entre processus. Dans le cadre du Brain, cette communication est entièrement transparente.
Lorsqu'un processus est lancé, une copie des attributs du Brain est créée et partagée entre tous les processus. Lorsque
l'un de ses attributs est modifié (que ce soit main_process → second_process ou second_process → main_process), le Brain
se charge automatiquement de synchroniser cette modification de la copie vers l'instance initiale. Cette copie partagée
est un dictionnaire proxy, un type issu de la classe Manager de la librairie multiprocessing.

> Limitation de la communication inter-process

La principale restriction quant à l’utilisation de cette fonctionnalité est le type des attributs de la classe pouvant
être partagés au travers du dictionnaire proxy. En effet, il faut que l’attribut soit sérialisable ! Les types
sérialisables supportés pour le moment sont :

```python
serialized_types = (
   Logger,  # Logger from loggerplusplus library is serialized since V0.1.2
   int,
   float,
   str,
   list,
   set,
   dict,
   tuple,
   type(None),
)
```

Il est donc compliqué de passer en attribut partagé un objet complexe à utiliser dans un autre processus. Pour
contourner ce problème, il est possible d’instancier directement dans le processus l’objet en question. Prenons
l’exemple de l’utilisation d’une caméra. Son utilisation est gourmande en ressources, donc idéale pour du
multiprocessing. Le problème est que l’objet caméra n’est pas sérialisable ! On va donc récupérer les éléments de
configuration de celle-ci via un attribut, puis l’instancier directement dans le processus.

```python
@Brain.task(process=True, run_on_start=[True / False])
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )
```

> Attention un process sera synchrone ! Pensez à mettre `def` et non `async def` !

On remarque que la configuration est directement accessible via `self` (qui accède en réalité à la copie partagée du
Brain). Une fois instanciée, nous utiliserons notre caméra pour capturer des images et y appliquer un traitement.
Cependant, cela pose un nouveau problème : le traitement doit s'exécuter en continu, nécessitant donc la création d'une
routine. Or, il n'est pas possible de créer une routine à l'intérieur d'une tâche, surtout si celle-ci est exécutée dans
un processus séparé. Pour répondre à ce besoin, une option appelée `define_loop_later` est disponible. Elle permet de
définir une tâche en tant que routine, tout en ayant une partie qui s'exécute une seule fois (comme la création de
l'objet caméra).

```python
@Brain.task(process=True, run_on_start=[True / False], refresh_rate=0.1, define_loop_later=True)
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )

   # ---Loop--- #
   camera.capture()
   # ... traitement d'image ... #
```

> Il faut penser à préciser notre `refresh_rate` car notre task est ici une routine ! (bien qu’elle ait une partie qui
> ne s’exécute qu’une seule fois)
> → On peut évidemment profiter de l’exécution hors du process principal pour diminuer fortement le `refresh_rate` afin
> d’avoir une routine qui s’exécute à haute fréquence.

Ici, on instancie notre caméra, puis on l’utilise pour prendre des photos et leur appliquer un traitement. Ce qui sépare
la partie one_shot de la routine est le commentaire `# ---Loop--- #`. En réalité, ce code très simple et léger
d’utilisation revient à faire ceci :

```python
@Brain.task(process=False, run_on_start=False)
async def one_shot_part(self):
   return Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )


@Brain.task(process=False, run_on_start=False, refresh_rate=0.1)
async def routine_part(self, camera):
   camera.capture()
   # ... traitement d'image ... #


@Brain.task(process=True, run_on_start=[True / False])
def camera_in_other_process(self):
   camera = asyncio.run(self.one_shot_part())
   asyncio.run(self.routine_part())
```

Il est également possible de définir le marker de la routine soit même :

```python
@Brain.task(process=True, run_on_start=[True / False], refresh_rate=0.1, define_loop_later=True,
            start_loop_marker="#- My Custom Loop Marker -#")
def camera_in_other_process(self):
   camera = Camera(
      res_w=self.config.CAMERA_RESOLUTION[0],
      res_h=self.config.CAMERA_RESOLUTION[1],
      captures_path=self.config.CAMERA_SAVE_PATH,
      undistorted_coefficients_path=self.config.CAMERA_COEFFICIENTS_PATH,
   )

   #- My Custom Loop Marker -#
   camera.capture()

   # ... traitement d'image ... #
```

## Points de vigilances, limitations et précisions

Bien que l’utilisation du Brain soit pratique, certains points sont à surveiller pour en tirer son plein potentiel.

### Dynamic init

### Création automatique des attributs

Afin d’alléger le code de l’`__init__`qui consiste essentiellement à faire ça:

```python
def __init__(
        self,
        logger: Logger,
        obj1: type_obj1,
        obj2: type_obj2,
        obj3: type_obj3,
) -> None:
   self.logger = logger
   self.obj1 = obj1
   self.obj2 = obj2
   self.obj3 = obj3
   ...
```

L’`__init__` est rendu dynamique: il le fait automatiquement, il suffit donc d’écrire:

```python
def __init__(
        self,
        logger: Logger,
        obj1: type_obj1,
        obj2: type_obj2,
        obj3: type_obj3,
) -> None:
   super().__init__(logger, self)
```

### Création d’attributs de classe

Si l’on veut créer des attributs de classe dans l’`__init__` et que l’on souhaite qu’ils soient partagés entre les
process, il faut les définir AVANT `super().__init__(logger, self)` . Dans le cas contraire ils seront disponibles
uniquement dans le main-process.

```python
def __init__(
        self,
        logger: Logger,
        obj1: type_obj1,
        obj2: type_obj2,
        obj3: type_obj3,
) -> None:
   # Attributs disponibles dans tous les process
   self.attr_multi_process = 0

   super().__init__(logger, self)

   # Attributs disponibles uniquement dans le main-process
   self.attr_main_process = 0
```

### Sérialisation des attributs

Lors de l’appel de l’`__init__`, le Brain se charge également de sérialiser automatiquement tous les attributs de
classe. Cependant, la majorité des objets que nous manipulons ne sont pas sérialisables. Un warning sera alors affiché
par le logger pour tout attribut non sérialisable. Ce n’est pas une erreur, juste un avertissement. Tout attribut non
sérialisé sera évidemment indisponible dans d’autres processus. Exemple de warning :

```
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_cmd].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_pami].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_lidar].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_odometer].
14:49:30 -> [   brain    ]  WARNING   | [dynamic_init] cannot serialize attribute [ws_camera].
```

### Refresh_Rate limitations

L'exécution des tâches repose sur de l'exécution asynchrone, ce qui signifie qu'il s'agit de pseudo-parallélisme. Il est
crucial de garder à l'esprit qu'une routine avec un `refresh_rate` très faible va monopoliser le temps CPU disponible
et, dans certains cas, ralentir l'exécution globale du Brain. Il est donc interdit de mettre un `refresh_rate` à 0 ! Ce
paramètre doit être réglé avec attention.

### Communication inter-process limitations

Comme expliqué précédemment, la synchronisation entre le Brain partagé et son instance s'effectue via une routine qui s'
exécute à très haute fréquence afin de minimiser la latence de communication. Par défaut, son `refresh_rate` est fixé à
0,01 seconde. Bien que la méthode soit optimisée pour réduire au maximum sa durée d'exécution, ce n'est pas instantané !
Il est donc important de prendre en compte ce facteur lorsqu'on décide de passer un traitement dans un autre processus.

## Exemple complet d’utilisation

Voici un exemple complet d'utilisation de votre module Brain avec une explication de son utilisation dans un script
principal.

```python
import asyncio
from taskbrain import Brain
from loggerplusplus import Logger


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
      self.logger.info("[MP] MainBrain started")
      public_attributes = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
      self.logger.info(f"[MP] Public attributes: {public_attributes}")

   """ Routine Tasks """

   @Brain.task(process=False, run_on_start=True, refresh_rate=1)
   async def mp_states_display(self):
      attributes_public = {k: v for k, v in self.__dict__.items() if
                           not k.startswith('_') and k.__str__() != "logger"}
      self.logger.info(f"[MP] Attributes states: {attributes_public}")

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
   """

   """ One-Shot Tasks """

   @Brain.task(process=True, run_on_start=True)
   def sb_start(self):
      self.logger.info("[SP] MainBrain started in another process")
      shared_attributes = {
         "share_attr1": self.share_attr1,
         "share_attr2": self.share_attr2
      }
      self.logger.info(f"[SP] Public attributes available in this subprocess: {shared_attributes}")

   """ Routine Tasks """

   @Brain.task(process=True, run_on_start=True, refresh_rate=1)
   def sp_states_display(self):
      shared_attributes = {
         "share_attr1": self.share_attr1,
         "share_attr2": self.share_attr2
      }
      self.logger.info(f"[SP] Attributes states: {shared_attributes}")

   @Brain.task(process=True, run_on_start=True, refresh_rate=1)
   def sb_incrementer(self):
      self.share_attr2 += 1

   @Brain.task(process=True, run_on_start=True, refresh_rate=1, timeout=5)
   def sb_incrementer_with_timeout(self):
      self.share_attr2 += 10

   @Brain.task(process=True, run_on_start=True, refresh_rate=1, define_loop_later=True,
               start_loop_marker="# ---Loop--- #")
   def sb_routine_with_setup(self):
      sb_non_serializable_attribute = "I'm not serializable attribute"
      # ---Loop--- #
      self.logger.info(f"[SP] Non-serializable attribute: {sb_non_serializable_attribute}")

   """ Call others tasks """

   @Brain.task(process=False, run_on_start=False)
   async def callable_function_1(self):
      self.logger.info("[MP] Callable function 1")
      return 1

   @Brain.task(process=True, run_on_start=False)
   def callable_function_2(self):
      self.logger.info("[SP] Callable function 2")
      return 2

   @Brain.task(process=False, run_on_start=True)
   async def call_tasks(self):
      await asyncio.sleep(10)  # Wait timed task to finish
      self.logger.info("[MP] Call tasks")
      f1_result = await self.callable_function_1()
      f2_result = await self.callable_function_2()

      self.logger.info(f"[MP] Callable function 1 result: {f1_result.result}")
      self.logger.info(f"[MP] Callable function 2 result: {f2_result.result}")
```

### Utilisation dans un Main

Voici comment vous pouvez intégrer et démarrer votre Brain dans un script principal :

```python
import asyncio
from exemple.mainbrain import MainBrain
from loggerplusplus import Logger

if __name__ == "__main__":
   brain_logger = Logger(
      identifier="Brain",
      print_log=True,
      write_to_file=False,
      display_monitoring=False,
      files_monitoring=False,
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
```

### Explication du Main

1. **Initialisation du Logger** : On crée un logger avec un niveau de débogage qui affiche les logs dans la
   console (`print_log=True`).
2. **Initialisation du Brain** : On initialise le `MainBrain` avec deux attributs partagés (`share_attr1`
   et `share_attr2`) et le logger.
3. **Exécution des Tâches** : On récupère toutes les tâches du Brain via `brain.get_tasks()` et on les exécute en les
   regroupant avec `asyncio.gather()`. Ce script illustre la manière dont vous pouvez initialiser et exécuter les
   différentes tâches de votre Brain, y compris les tâches asynchrones, les routines, et le multiprocessing.

Voici une suggestion pour une signature élégante à la fin de votre README:

---

## Auteur

Projet créé et maintenu par **Florian BARRE**.  
Pour toute question ou contribution, n'hésitez pas à me contacter.
[Mon Site](https://florianbarre.fr/) | [Mon LinkedIn](www.linkedin.com/in/barre-florian) | [Mon GitHub](https://github.com/Florian-BARRE)