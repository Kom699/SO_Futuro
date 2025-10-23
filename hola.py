import os
import time
import hashlib
from datetime import datetime
from enum import Enum
from collections import deque

class ProcessState(Enum):
    NEW = "Nuevo"
    READY = "Listo"
    RUNNING = "Ejecutando"
    WAITING = "Esperando"
    TERMINATED = "Terminado"

class Process:
    def __init__(self, pid, name, priority=1, memory_required=1024):
        self.pid = pid
        self.name = name
        self.state = ProcessState.NEW
        self.priority = priority
        self.memory_required = memory_required
        self.created_at = datetime.now()
        self.cpu_time_used = 0
        
    def __str__(self):
        return f"PID: {self.pid}, Nombre: {self.name}, Estado: {self.state.value}"

class ProcessScheduler:
    def __init__(self):
        self.ready_queue = deque()
        self.running_process = None
        self.processes = {}
        self.next_pid = 1
        self.quantum = 3
        
    def create_process(self, name, priority=1, memory=1024):
        pid = self.next_pid
        process = Process(pid, name, priority, memory)
        self.processes[pid] = process
        self.next_pid += 1
        process.state = ProcessState.READY
        self.ready_queue.append(process)
        print(f"Proceso creado: {process}")
        return pid
    
    def schedule(self):
        if self.running_process:
            if self.running_process.cpu_time_used < self.quantum:
                return self.running_process
            self.running_process.state = ProcessState.READY
            self.ready_queue.append(self.running_process)
        
        if self.ready_queue:
            sorted_queue = sorted(self.ready_queue, key=lambda x: x.priority, reverse=True)
            self.ready_queue = deque(sorted_queue)
            next_process = self.ready_queue.popleft()
            next_process.state = ProcessState.RUNNING
            self.running_process = next_process
            return next_process
        return None
    
    def execute_cycle(self):
        current_process = self.schedule()
        if current_process:
            current_process.cpu_time_used += 1
            print(f"Ejecutando: {current_process.name} (CPU time: {current_process.cpu_time_used})")
            if current_process.cpu_time_used >= 5:
                self.terminate_process(current_process.pid)
        else:
            print("No hay procesos en cola")
    
    def terminate_process(self, pid):
        if pid in self.processes:
            process = self.processes[pid]
            process.state = ProcessState.TERMINATED
            if self.running_process and self.running_process.pid == pid:
                self.running_process = None
            print(f"Proceso terminado: {process.name}")

class MemoryManager:
    def __init__(self, total_memory=1024 * 1024):
        self.total_memory = total_memory
        self.available_memory = total_memory
        self.memory_map = {}
        self.page_size = 4096
        
    def allocate_memory(self, process, size):
        if size > self.available_memory:
            raise MemoryError("Memoria insuficiente")
        pages_needed = (size + self.page_size - 1) // self.page_size
        allocated_pages = []
        for i in range(pages_needed):
            page_id = len(self.memory_map)
            self.memory_map[page_id] = {'process': process.pid, 'allocated_at': datetime.now()}
            allocated_pages.append(page_id)
        self.available_memory -= pages_needed * self.page_size
        print(f"Memoria asignada: {pages_needed} paginas para {process.name}")
        return allocated_pages
    
    def free_memory(self, process_pid):
        pages_to_free = [pid for pid, info in self.memory_map.items() if info['process'] == process_pid]
        for page_id in pages_to_free:
            del self.memory_map[page_id]
            self.available_memory += self.page_size
        print(f"Memoria liberada: {len(pages_to_free)} paginas del proceso {process_pid}")

class FileSystem:
    def __init__(self):
        self.files = {}
        self.directories = {'/': {'type': 'directory', 'children': {}}}
        self.current_directory = '/'
        
    def create_file(self, filename, content=""):
        filepath = os.path.join(self.current_directory, filename).replace('\\', '/')
        self.files[filepath] = {
            'content': content,
            'created_at': datetime.now(),
            'size': len(content),
            'type': 'file'
        }
        print(f"Archivo creado: {filepath}")
    
    def list_directory(self, path='.'):
        if path == '.':
            path = self.current_directory
        contents = []
        for item_path, info in self.files.items():
            if os.path.dirname(item_path) == path:
                contents.append((os.path.basename(item_path), 'file'))
        print(f"Contenido de {path}:")
        for name, type_ in contents:
            print(f"  {name} ({type_})")

class SecurityManager:
    def __init__(self):
        self.users = {}
        self.sessions = {}
        
    def create_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = {'hashed_password': hashed_password, 'created_at': datetime.now()}
        print(f"Usuario creado: {username}")
    
    def authenticate(self, username, password):
        if username not in self.users:
            return False
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if self.users[username]['hashed_password'] == hashed_input:
            session_id = hashlib.md5(f"{username}{datetime.now()}".encode()).hexdigest()
            self.sessions[session_id] = {'username': username, 'login_time': datetime.now()}
            print(f"Autenticacion exitosa: {username}")
            return session_id
        return False

class NexusCLI:
    def __init__(self, os_instance):
        self.os = os_instance
        self.current_user = None
        self.session_id = None
        
    def start_cli(self):
        print("NEXUS OS - Interfaz de Comandos")
        print("Comandos: login, run, list, create, meminfo, exit")
        
        while True:
            try:
                if self.current_user:
                    prompt = f"nexus@{self.current_user}> "
                else:
                    prompt = "nexus@guest> "
                
                command = input(prompt).strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                args = command[1:]
                
                if cmd == 'exit':
                    break
                elif cmd == 'login':
                    self.handle_login(args)
                elif cmd == 'run':
                    self.handle_run_process(args)
                elif cmd == 'list':
                    self.handle_list(args)
                elif cmd == 'create':
                    self.handle_create_file(args)
                elif cmd == 'meminfo':
                    self.show_memory_info()
                elif cmd == 'help':
                    self.show_help()
                else:
                    print(f"Comando no reconocido: {cmd}")
                    
            except KeyboardInterrupt:
                print("Saliendo de Nexus OS...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def handle_login(self, args):
        if len(args) < 2:
            print("Uso: login <usuario> <contrasena>")
            return
        username, password = args[0], args[1]
        session_id = self.os.security.authenticate(username, password)
        if session_id:
            self.current_user = username
            self.session_id = session_id
        else:
            print("Autenticacion fallida")
    
    def handle_run_process(self, args):
        if not args:
            print("Uso: run <nombre_del_proceso>")
            return
        process_name = args[0]
        priority = int(args[1]) if len(args) > 1 else 1
        self.os.scheduler.create_process(process_name, priority)
    
    def handle_list(self, args):
        if not args or args[0] == 'processes':
            print("Procesos en el sistema:")
            for pid, process in self.os.scheduler.processes.items():
                print(f"  {process}")
        elif args[0] == 'files':
            self.os.filesystem.list_directory()
    
    def handle_create_file(self, args):
        if len(args) < 1:
            print("Uso: create <nombre_archivo> [contenido]")
            return
        filename = args[0]
        content = args[1] if len(args) > 1 else ""
        self.os.filesystem.create_file(filename, content)
    
    def show_memory_info(self):
        memory = self.os.memory_manager
        used = memory.total_memory - memory.available_memory
        print("Informacion de Memoria:")
        print(f"  Total: {memory.total_memory} bytes")
        print(f"  Usada: {used} bytes")
        print(f"  Disponible: {memory.available_memory} bytes")
        print(f"  Paginas asignadas: {len(memory.memory_map)}")
    
    def show_help(self):
        print("Comandos disponibles:")
        print("  login <user> <pass>  - Iniciar sesion")
        print("  run <name> [pri]     - Ejecutar proceso")
        print("  list processes       - Listar procesos")
        print("  list files           - Listar archivos")
        print("  create <file> [cont] - Crear archivo")
        print("  meminfo              - Info de memoria")
        print("  exit                 - Salir del sistema")

class NexusOS:
    def __init__(self):
        self.name = "NexusOS"
        self.version = "1.0"
        self.scheduler = ProcessScheduler()
        self.memory_manager = MemoryManager()
        self.filesystem = FileSystem()
        self.security = SecurityManager()
        self.cli = NexusCLI(self)
        self.initialize_system()
    
    def initialize_system(self):
        print(f"Iniciando {self.name} v{self.version}")
        self.security.create_user("admin", "admin123")
        self.security.create_user("usuario", "clave123")
        self.filesystem.create_file("readme.txt", "Bienvenido a NexusOS")
        self.filesystem.create_file("system.log", "Log del sistema")
    
    def run_simulation(self):
        print("MODO SIMULACION DEL SISTEMA")
        processes = [("navegador", 2), ("editor", 1), ("calculadora", 1), ("reproductor", 3)]
        for name, priority in processes:
            self.scheduler.create_process(name, priority)
        for i in range(10):
            print(f"Ciclo {i+1}")
            self.scheduler.execute_cycle()
            time.sleep(1)
    
    def start_system(self):
        self.run_simulation()
        self.cli.start_cli()

if __name__ == "__main__":
    try:
        nexus_os = NexusOS()
        nexus_os.start_system()
    except Exception as e:
        print(f"Error critico en el sistema: {e}")