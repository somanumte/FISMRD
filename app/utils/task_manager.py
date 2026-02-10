# -*- coding: utf-8 -*-
import threading
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Gestor de tareas en segundo plano simple basado en hilos.
    Permite ejecutar funciones sin bloquear el hilo principal de la solicitud.
    """
    
    _executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="bg_task")
    _active_tasks = {} # task_id -> task_info

    @staticmethod
    def run_async(func, *args, **kwargs):
        """
        Ejecuta una función en segundo plano.
        
        Args:
            func: La función a ejecutar.
            *args, **kwargs: Argumentos para la función.
            
        Returns:
            str: ID de la tarea generada.
        """
        task_id = str(uuid.uuid4())
        
        def task_wrapper():
            logger.info(f"🚀 Iniciando tarea en background: {task_id}")
            try:
                TaskManager._active_tasks[task_id] = {'status': 'running', 'name': func.__name__}
                func(*args, **kwargs)
                logger.info(f"✅ Tarea {task_id} completada exitosamente.")
                TaskManager._active_tasks[task_id]['status'] = 'completed'
            except Exception as e:
                logger.error(f"❌ Error en tarea {task_id}: {str(e)}", exc_info=True)
                TaskManager._active_tasks[task_id] = {'status': 'failed', 'error': str(e)}
        
        TaskManager._executor.submit(task_wrapper)
        return task_id

    @staticmethod
    def get_task_status(task_id):
        """Retorna el estado de una tarea."""
        return TaskManager._active_tasks.get(task_id, {'status': 'not_found'})
