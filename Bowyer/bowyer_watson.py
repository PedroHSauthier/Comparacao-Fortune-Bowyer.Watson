"""
Implementação do Algoritmo de Bowyer-Watson para Geração de Triangulação de Delaunay
e o subsequente Diagrama de Voronoi (seu dual).

Este script foi projetado para fins académicos, focando na clareza da implementação
dos conceitos fundamentais do algoritmo incremental.
"""

import math
import time
import tracemalloc
import random
import sys
import numpy as np
from collections import namedtuple

# --- Estruturas de Dados e Classes Auxiliares ---

Point = namedtuple('Point', ['x', 'y'])
Edge = namedtuple('Edge', ['v1', 'v2'])

class Triangle:
    """
    Representa um triângulo na triangulação. Contém 3 vértices e armazena seu circuncírculo.
    """
    def __init__(self, v1, v2, v3):
        # Garante a ordem dos vértices para consistència
        self.vertices = tuple(sorted((v1, v2, v3)))
        self.circumcenter, self.circumradius_sq = self._calculate_circumcircle()

    def __eq__(self, other):
        return self.vertices == other.vertices

    def __hash__(self):
        return hash(self.vertices)

    def _calculate_circumcircle(self):
        """ Calcula o centro e o raio ao quadrado do círculo que passa pelos 3 vértices. """
        p1, p2, p3 = self.vertices
        D = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))
        
        if abs(D) < 1e-10: # Pontos colineares
            return None, float('inf')

        p1_sq = p1.x**2 + p1.y**2
        p2_sq = p2.x**2 + p2.y**2
        p3_sq = p3.x**2 + p3.y**2

        ux = (p1_sq * (p2.y - p3.y) + p2_sq * (p3.y - p1.y) + p3_sq * (p1.y - p2.y)) / D
        uy = (p1_sq * (p3.x - p2.x) + p2_sq * (p1.x - p3.x) + p3_sq * (p2.x - p1.x)) / D
        
        center = Point(ux, uy)
        radius_sq = (p1.x - ux)**2 + (p1.y - uy)**2
        
        return center, radius_sq

    def point_in_circumcircle(self, point):
        """ Verifica se um ponto está dentro do circuncírculo deste triângulo. """
        if self.circumcenter is None:
            return False
        dist_sq = (point.x - self.circumcenter.x)**2 + (point.y - self.circumcenter.y)**2
        return dist_sq < self.circumradius_sq

# --- Classe Principal do Algoritmo ---

class BowyerWatson:
    """
    Encapsula o estado e a lógica do algoritmo de Bowyer-Watson.
    """
    def __init__(self, points):
        self.points = [Point(p[0], p[1]) for p in points]
        self.triangulation = set()
        self.voronoi_edges = []

        # Métricas
        self.metrics = {
            "num_sites": len(points),
            "delaunay_triangles": 0,
            "voronoi_vertices": 0,
            "voronoi_edges_created": 0
        }

    def run(self):
        """ Executa o algoritmo principal. """
        start_time = time.perf_counter()
        tracemalloc.start()

        # 1. Inicializa com um super-triângulo que envolve todos os pontos
        super_triangle, super_vertices = self._create_super_triangle()
        self.triangulation.add(super_triangle)

        # 2. Adiciona cada ponto incrementalmente
        for point in self.points:
            bad_triangles = set()
            # Encontra triângulos cujo circuncírculo contém o ponto
            for triangle in self.triangulation:
                if triangle.point_in_circumcircle(point):
                    bad_triangles.add(triangle)

            # Encontra a borda do "buraco" poligonal
            polygon_boundary = set()
            for triangle in bad_triangles:
                for i in range(3):
                    v1 = triangle.vertices[i]
                    v2 = triangle.vertices[(i + 1) % 3]
                    edge = Edge(*tuple(sorted((v1, v2))))
                    if edge in polygon_boundary:
                        polygon_boundary.remove(edge)
                    else:
                        polygon_boundary.add(edge)
            
            # Remove os triângulos "ruins"
            self.triangulation -= bad_triangles

            # Retriangula o buraco
            for edge in polygon_boundary:
                new_triangle = Triangle(edge.v1, edge.v2, point)
                self.triangulation.add(new_triangle)

        # 3. Remove triângulos que compartilham vértices com o super-triângulo
        self.triangulation = {tri for tri in self.triangulation if not any(v in super_vertices for v in tri.vertices)}

        # 4. Deriva o diagrama de Voronoi a partir da triangulação de Delaunay
        self._derive_voronoi_diagram()

        # Coleta de métricas
        self.metrics["delaunay_triangles"] = len(self.triangulation)
        self.metrics["voronoi_vertices"] = len(self.triangulation) # Cada triângulo de Delaunay gera um vértice de Voronoi
        self.metrics["voronoi_edges_created"] = len(self.voronoi_edges)

    def _create_super_triangle(self):
        """ Cria um triângulo grande o suficiente para conter todos os pontos. """
        min_x = min(p.x for p in self.points)
        max_x = max(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_y = max(p.y for p in self.points)

        dx = max_x - min_x
        dy = max_y - min_y
        delta_max = max(dx, dy)
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        # Vértices do super-triângulo
        v1 = Point(mid_x - 20 * delta_max, mid_y - 10 * delta_max)
        v2 = Point(mid_x + 20 * delta_max, mid_y - 10 * delta_max)
        v3 = Point(mid_x, mid_y + 20 * delta_max)
        
        return Triangle(v1, v2, v3), {v1, v2, v3}

    def _derive_voronoi_diagram(self):
        """ Constrói as arestas de Voronoi a partir da triangulação de Delaunay final. """
        # Mapeia arestas de Delaunay para os triângulos que as compartilham
        edge_to_triangles = {}
        for tri in self.triangulation:
            for i in range(3):
                v1 = tri.vertices[i]
                v2 = tri.vertices[(i + 1) % 3]
                edge = Edge(*tuple(sorted((v1, v2))))
                if edge not in edge_to_triangles:
                    edge_to_triangles[edge] = []
                edge_to_triangles[edge].append(tri)
        
        # Arestas de Voronoi conectam os circocentros de triângulos adjacentes
        for edge, triangles in edge_to_triangles.items():
            if len(triangles) == 2:
                p1 = triangles[0].circumcenter
                p2 = triangles[1].circumcenter
                if p1 and p2:
                    self.voronoi_edges.append((p1, p2))

# --- Bloco de Execução Principal ---

if __name__ == "__main__":
    print("Executando o Algoritmo de Bowyer-Watson para Diagrama de Voronoi...")

    # 1. Geração de Sítios
    random.seed(42)
    NUM_SITES = 500
    points = np.array([[random.uniform(0, 800), random.uniform(0, 600)] for _ in range(NUM_SITES)])

    # 2. Execução do Algoritmo
    bw_generator = BowyerWatson(points)
    bw_generator.run()

    # 3. Exibição das Métricas
    print("\n--- Métricas da Execução ---")
    metrics = bw_generator.metrics
    for key, value in metrics.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value:.4f}" if isinstance(value, float) else f"{key.replace('_', ' ').capitalize()}: {value}")

    # 4. Visualização com Matplotlib
    try:
        import matplotlib.pyplot as plt
        
        print("\nGerando visualização com Matplotlib...")
        fig, ax = plt.subplots()
        
        # Plota os sítios
        ax.plot(points[:, 0], points[:, 1], 'o', color='red', label='Sítios')

        # Plota as arestas do diagrama de Voronoi
        for p1, p2 in bw_generator.voronoi_edges:
            ax.plot([p1.x, p2.x], [p1.y, p2.y], 'b-')

        ax.set_title(f'Diagrama de Voronoi (Bowyer-Watson) com {NUM_SITES} sítios')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('equal', adjustable='box')
        ax.legend()
        plt.grid(True)
        
        # Define os limites do gráfico
        min_x, max_x = points[:, 0].min(), points[:, 0].max()
        min_y, max_y = points[:, 1].min(), points[:, 1].max()
        dx = (max_x - min_x) * 0.1
        dy = (max_y - min_y) * 0.1
        ax.set_xlim(min_x - dx, max_x + dx)
        ax.set_ylim(min_y - dy, max_y + dy)

        plt.show()

    except ImportError:
        print("\nMatplotlib não encontrado. Pule a etapa de visualização.")
        print("Para visualizar o diagrama, instale a biblioteca: pip install matplotlib numpy")
