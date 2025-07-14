import tkinter as tk
from tkinter import messagebox
import time
import random
import heapq
from collections import deque
from abc import ABC, abstractmethod

# constantes de mapa 
MAX_SIZE = 30
SIZE_CELL = 25

FREE, BUILDING, WATER, BLOCKED, ENTRY, EXIT, PATH, SEARCHING = 0, 1, 2, 3, 4, 5, 9, 8

colors = {
    FREE: "white",
    BUILDING:"black",
    WATER: "blue",
    BLOCKED: "orange",
    ENTRY: "green",
    EXIT: "red",
    PATH: "purple",
    SEARCHING: "#ADD8E6"
}

cost = {
    FREE: 1,
    BUILDING: float("inf"),
    WATER: 5,
    BLOCKED: 10,
    ENTRY: 0,
    EXIT: 0,
    SEARCHING: 1
}

# Clase mapa 
class Mapa:
    def __init__(self, filas, columnas):
        self.filas = filas
        self.columnas = columnas
        self.matriz = [[FREE for _ in range(columnas)] for _ in range(filas)]
        self.original_types = {}

    def set_type(self, fila, col, tipo):
        if tipo in (ENTRY, EXIT):
            self.clear_tipo(tipo)
        self.matriz[fila][col] = tipo

    def clear_tipo(self, tipo):
        for i in range(self.filas):
            for j in range(self.columnas):
                if self.matriz[i][j] == tipo:
                    self.matriz[i][j] = FREE

    def draw(self, canvas):
        canvas.delete("all")
        for i in range(self.filas):
            for j in range(self.columnas):
                tipo = self.matriz[i][j]
                canvas.create_rectangle(
                    j * SIZE_CELL, i * SIZE_CELL,
                    (j + 1) * SIZE_CELL, (i + 1) * SIZE_CELL,
                    fill=colors.get(tipo, "gray"),
                    outline="gray"
                )

    def randomize(self):
        for i in range(self.filas):
            for j in range(self.columnas):
                if self.matriz[i][j] in (ENTRY, EXIT):
                    continue
                self.matriz[i][j] = random.choices(
                    [FREE, BUILDING, WATER, BLOCKED],
                    weights=[0.6, 0.2, 0.1, 0.1]
                )[0]

    def find_entry_exit(self):
        entry = exit_ = None
        for i in range(self.filas):
            for j in range(self.columnas):
                if self.matriz[i][j] == ENTRY:
                    entry = (i, j)
                elif self.matriz[i][j] == EXIT:
                    exit_ = (i, j)
        return entry, exit_
    
    def clean_visuals(self):
        self.original_types.clear()
        for i in range(self.filas):
            for j in range(self.columnas):
                if self.matriz[i][j] in (PATH, SEARCHING):
                    self.matriz[i][j] = FREE

    def animate(self, x, y, canvas, root):
        if self.matriz[x][y] not in (ENTRY, EXIT):
            if (x, y) not in self.original_types:
                self.original_types[(x, y)] = self.matriz[x][y]
            self.matriz[x][y] = SEARCHING
            self.draw(canvas)
            root.update()
            time.sleep(0.01)

    def mark_path(self, came_from, start, end):
        actual = end
        while actual != start:
            x, y = actual
            if self.matriz[x][y] not in (ENTRY, EXIT):
                self.matriz[x][y] = PATH
            actual = came_from[actual]


#clase para algoritmo de busqueda
class SearchAlgorithm(ABC):
    def __init__(self, mapa, canvas, root):
        self.mapa = mapa
        self.canvas = canvas
        self.root = root

    @abstractmethod
    def search(self):
        pass


# Algoritmo BFS
class BFS(SearchAlgorithm):
    def search(self):
        entry, exit_ = self.mapa.find_entry_exit()
        if not entry or not exit_:
            messagebox.showerror("Error", "Falta entrada o salida")
            return
        
        self.mapa.clean_visuals()
        start = time.time()
        queue = deque([entry])
        visited = {entry}
        came_from = {}

        while queue:
            actual = queue.popleft()
            if actual == exit_:
                break

            x, y = actual
            for dx, dy in [(-1,0),(0,-1),(1,0),(0,1)]:
                nx, ny = x + dx, y + dy
                next_cell = (nx, ny)
                if 0 <= nx < self.mapa.filas and 0 <= ny < self.mapa.columnas:
                    if self.mapa.matriz[nx][ny] in (FREE, EXIT) and next_cell not in visited:
                        visited.add(next_cell)
                        came_from[next_cell] = actual
                        queue.append(next_cell)
                        self.mapa.animate(nx, ny, self.canvas, self.root)

        self.mapa.mark_path(came_from, entry, exit_)
        self.mapa.draw(self.canvas)
        messagebox.showinfo('Resultado', f'BFS: {time.time() - start:.3f}s')


class Dijkstra(SearchAlgorithm):
    def search(self):
        entry, exit_ = self.mapa.find_entry_exit()
        if not entry or not exit_:
            messagebox.showerror('Error', 'Falta entrada o salida')
            return
        
        self.mapa.clean_visuals()
        start = time.time()
        heap = [(0, entry)]
        came_from = {}
        visited = set()
        cost_so_far = {entry: 0}

        while heap:
            _, actual = heapq.heappop(heap)
            if actual in visited:
                continue
            visited.add(actual)

            if actual == exit_:
                break

            x, y = actual
            for dx, dy in [(-1,0),(0,-1),(1,0),(0,1)]:
                nx, ny = x + dx, y + dy
                next_cell = (nx,ny)
                if 0 <= nx < self.mapa.filas and 0 <= ny < self.mapa.columnas:
                    original = self.mapa.original_types.get((nx, ny), self.mapa.matriz[nx][ny])
                    new_cost = cost_so_far[actual] + cost[original]
                    if self.mapa.matriz[nx][ny] != BUILDING and (next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]):
                        cost_so_far[next_cell] = new_cost
                        came_from[next_cell] = actual
                        heapq.heappush(heap, (new_cost, next_cell))
                        self.mapa.animate(nx, ny, self.canvas, self.root)

        self.mapa.mark_path(came_from, entry, exit_)
        self.mapa.draw(self.canvas)
        messagebox.showinfo('Resultado', f'Dijkstra: {time.time() - start:.3f}s')


class AStar(SearchAlgorithm):
    def search(self):
        entry, exit_ = self.mapa.find_entry_exit()
        if not entry or not exit_:
            messagebox.showerror('Error', 'Falta entrada o salida')
            return
        
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        self.mapa.clean_visuals()
        start = time.time()
        heap = [(0, entry)]
        came_from = {}
        visited = set()
        cost_so_far = {entry: 0}

        while heap:
            _, actual = heapq.heappop(heap)
         
            if actual == exit_:
                break
        
            if actual in visited:
                continue
            visited.add(actual)

            x, y = actual
            for dx, dy in [(-1,0),(0,-1),(1,0),(0,1)]:
                nx, ny = x + dx, y + dy
                next_cell = (nx, ny)
                if 0 <= nx < self.mapa.filas and 0 <= ny < self.mapa.columnas:
                    original = self.mapa.original_types.get((nx, ny), self.mapa.matriz[nx][ny])
                    new_cost = cost_so_far[actual] + cost[original]
                    if self.mapa.matriz[nx][ny] != BUILDING and (next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]):
                        cost_so_far[next_cell] = new_cost
                        priority = new_cost + heuristic(next_cell, exit_)
                        heapq.heappush(heap, (priority, next_cell))
                        came_from[next_cell] = actual
                        self.mapa.animate(nx, ny, self.canvas, self.root)

        if exit_ in came_from:
            self.mapa.mark_path(came_from, entry, exit_)
            self.mapa.draw(self.canvas)
            messagebox.showinfo('Resultado', f'A* {time.time() - start:.3f}s')
        else:
            messagebox.showwarning('Sin camino', 'No se encontro un camino hasta la salida')


#clase principal que une todo
class RouteCalculator:
    def __init__(self, root):
        self.root = root
        self.mapa = Mapa(10, 10)
        self.canvas = tk.Canvas(root, width=10 * SIZE_CELL, height=10 * SIZE_CELL, bg='white')
        self.canvas.pack(side='right', padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)


        self.current_type = FREE 
        self.current_algorithm = "BFS"

        self.build_ui()
        self.mapa.draw(self.canvas)

    def build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(side='left', padx=10, pady=10)

        def add_button(text,command):
            tk.Button(frame, text=text, command=command).pack(fill="x")


        tk.Label(frame, text='Tipo de celda: ').pack()
        add_button("Libre", lambda: self.set_type(FREE))
        add_button("Edificio", lambda: self.set_type(BUILDING))
        add_button("Agua", lambda: self.set_type(WATER))
        add_button("Bloqueado", lambda: self.set_type(BLOCKED))
        tk.Label(frame, text='').pack()
        add_button("Entrada", lambda: self.set_type(ENTRY))
        add_button("Salida", lambda: self.set_type(EXIT))


        tk.Label(frame, text="\nTamanho del mapa").pack()
        self.entry_rows = tk.Entry(frame)
        self.entry_rows.insert(0, '10')
        self.entry_rows.pack()
        self.entry_columns = tk.Entry(frame)
        self.entry_columns.insert(0, '10')
        self.entry_columns.pack()


        add_button('Generar mapa', self.generate_map)
        add_button('Randomizar', self.randomizer)
        add_button('Calcular ruta', self.execute_algorithm)


        tk.Label(frame, text=f'Algoritmo actual: {self.current_algorithm}').pack()
        add_button('BFS', lambda: self.set_algorithm('BFS'))
        add_button('Dijkstra', lambda: self.set_algorithm('Dijkstra'))
        add_button('A*', lambda: self.set_algorithm('A*'))


    def set_type(self, tipo):
        self.current_type = tipo

    def set_algorithm(self, name):
        self.current_algorithm = name

    def generate_map(self): 
        try:
            f = int(self.entry_rows.get())
            c = int(self.entry_columns.get())
            if not (5 <= f <= MAX_SIZE and 5 <= c <= MAX_SIZE):
                raise ValueError
        except ValueError:
            messagebox.showerror('Error', 'Tamanho invalido')
            return
        
        self.mapa = Mapa(f, c)
        self.canvas.config(width=c * SIZE_CELL, height=f * SIZE_CELL)
        self.mapa.draw(self.canvas)

    def randomizer(self):
        self.mapa.randomize()
        self.mapa.draw(self.canvas)

    def on_click(self, event):
        fila = event.y // SIZE_CELL
        col = event.x // SIZE_CELL
        if 0 <= fila < self.mapa.filas and 0 <= col < self.mapa.columnas:
            self.mapa.set_type(fila, col, self.current_type)
            self.mapa.draw(self.canvas)

    def execute_algorithm(self):
        algorithm = None
        if self.current_algorithm == 'BFS':
            algorithm = BFS(self.mapa, self.canvas, self.root)
        elif self.current_algorithm == 'Dijkstra':
            algorithm = Dijkstra(self.mapa, self.canvas, self.root)
        elif self.current_algorithm == 'A*':
            algorithm = AStar(self.mapa, self.canvas, self.root)

        if algorithm:
            algorithm.search()

#iniciar
if __name__ == "__main__":
    root = tk.Tk()
    root.title('Route Calculator ')
    app = RouteCalculator(root)
    root.mainloop()
