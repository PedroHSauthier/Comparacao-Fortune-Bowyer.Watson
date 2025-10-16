"""
Implementação do Algoritmo de Bowyer-Watson com Saída Detalhada dos Cálculos Matemáticos.

Este script executa o algoritmo passo a passo e imprime as fórmulas e valores
utilizados em cada etapa crítica, como o cálculo de circuncírculos e a verificação
de pontos.
"""

import math
import random
from collections import namedtuple

# --- Estruturas de Dados ---
Point = namedtuple('Point', ['x', 'y'])
Edge = namedtuple('Edge', ['v1', 'v2'])

class Triangle:
    """
    Representa um triângulo e armazena detalhes sobre seu circuncírculo para fins de depuração.
    """
    def __init__(self, v1, v2, v3, verbose=False):
        self.vertices = tuple(sorted((v1, v2, v3)))
        self.verbose = verbose
        self.circumcenter, self.circumradius_sq = self._calculate_circumcircle()

    def __eq__(self, other):
        return self.vertices == other.vertices

    def __hash__(self):
        return hash(self.vertices)

    def _calculate_circumcircle(self):
        """
        Calcula o centro e o raio ao quadrado do circuncírculo.
        Imprime cada passo do cálculo se verbose=True.
        """
        p1, p2, p3 = self.vertices
        
        if self.verbose:
            print(f"\n--- Calculando Circuncírculo para Triângulo com vértices: {p1}, {p2}, {p3} ---")

        # Fórmula do denominador D
        D = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))
        if self.verbose:
            print(f"  D = 2 * ({p1.x} * ({p2.y} - {p3.y}) + {p2.x} * ({p3.y} - {p1.y}) + {p3.x} * ({p1.y} - {p2.y})) = {D:.4f}")

        if abs(D) < 1e-10:
            if self.verbose:
                print("  Vértices são colineares. Circuncírculo indefinido.")
            return None, float('inf')

        # Quadrado das coordenadas
        p1_sq = p1.x**2 + p1.y**2
        p2_sq = p2.x**2 + p2.y**2
        p3_sq = p3.x**2 + p3.y**2
        if self.verbose:
            print(f"  p1_sq = {p1.x}^2 + {p1.y}^2 = {p1_sq:.4f}")
            print(f"  p2_sq = {p2.x}^2 + {p2.y}^2 = {p2_sq:.4f}")
            print(f"  p3_sq = {p3.x}^2 + {p3.y}^2 = {p3_sq:.4f}")

        # Fórmula do centro (ux, uy)
        ux = (p1_sq * (p2.y - p3.y) + p2_sq * (p3.y - p1.y) + p3_sq * (p1.y - p2.y)) / D
        uy = (p1_sq * (p3.x - p2.x) + p2_sq * (p1.x - p3.x) + p3_sq * (p2.x - p1.x)) / D
        if self.verbose:
            print(f"  ux = ({p1_sq:.2f}*({p2.y - p3.y}) + {p2_sq:.2f}*({p3.y - p1.y}) + {p3_sq:.2f}*({p1.y - p2.y})) / {D:.2f} = {ux:.4f}")
            print(f"  uy = ({p1_sq:.2f}*({p3.x - p2.x}) + {p2_sq:.2f}*({p1.x - p3.x}) + {p3_sq:.2f}*({p2.x - p1.x})) / {D:.2f} = {uy:.4f}")

        center = Point(ux, uy)
        
        # Fórmula do raio ao quadrado
        radius_sq = (p1.x - ux)**2 + (p1.y - uy)**2
        if self.verbose:
            print(f"  Raio^2 = ({p1.x} - {ux:.2f})^2 + ({p1.y} - {uy:.2f})^2 = {radius_sq:.4f}")
            print(f"  Circuncentro: {center}, Raio ao Quadrado: {radius_sq:.4f}")

        return center, radius_sq

    def point_in_circumcircle(self, point):
        """
        Verifica se um ponto está dentro do circuncírculo, mostrando os cálculos.
        """
        if self.circumcenter is None:
            return False
            
        dist_sq = (point.x - self.circumcenter.x)**2 + (point.y - self.circumcenter.y)**2
        
        if self.verbose:
            print(f"\n  Verificando Ponto {point} no circuncírculo do triângulo {self.vertices}:")
            print(f"    Distância^2 = ({point.x} - {self.circumcenter.x:.2f})^2 + ({point.y} - {self.circumcenter.y:.2f})^2 = {dist_sq:.4f}")
            print(f"    Comparando: Distância^2 ({dist_sq:.4f}) < Raio^2 ({self.circumradius_sq:.4f})")
            if dist_sq < self.circumradius_sq:
                print("    Resultado: Ponto ESTÁ DENTRO do circuncírculo (Triângulo Ruim).")
            else:
                print("    Resultado: Ponto NÃO está dentro do circuncírculo.")

        return dist_sq < self.circumradius_sq

class BowyerWatsonDetailed:
    def __init__(self, points):
        self.points = [Point(p[0], p[1]) for p in points]
        self.triangulation = set()

    def run(self, verbose=False):
        print("--- INICIANDO ALGORITMO DE BOWYER-WATSON ---")
        
        # 1. Cria um super-triângulo
        super_triangle, super_vertices = self._create_super_triangle(verbose)
        self.triangulation.add(Triangle(super_triangle[0], super_triangle[1], super_triangle[2], verbose=verbose))
        
        if verbose:
            print(f"\n[PASSO 1] Super-triângulo criado com vértices: {super_triangle}")

        # 2. Adiciona cada ponto
        for i, point in enumerate(self.points):
            if verbose:
                print(f"\n\n--- [PASSO 2.{i+1}] Adicionando Ponto: {point} ---")
            
            bad_triangles = set()
            for triangle in self.triangulation:
                if triangle.point_in_circumcircle(point):
                    bad_triangles.add(triangle)
            
            if verbose:
                print(f"\n  Encontrados {len(bad_triangles)} triângulos 'ruins' para remover.")

            # Encontra a borda do polígono
            polygon_boundary = set()
            for triangle in bad_triangles:
                for j in range(3):
                    v1 = triangle.vertices[j]
                    v2 = triangle.vertices[(j + 1) % 3]
                    edge = Edge(*tuple(sorted((v1, v2))))
                    if edge in polygon_boundary:
                        polygon_boundary.remove(edge)
                    else:
                        polygon_boundary.add(edge)
            
            if verbose:
                print(f"  A borda do 'buraco' poligonal tem {len(polygon_boundary)} arestas.")

            # Remove triângulos ruins
            self.triangulation -= bad_triangles

            # Retriangula
            if verbose:
                print("  Retriangulando o buraco...")
            for edge in polygon_boundary:
                new_triangle = Triangle(edge.v1, edge.v2, point, verbose=verbose)
                self.triangulation.add(new_triangle)
                if verbose:
                    print(f"    Novo triângulo criado: {new_triangle.vertices}")

        # 3. Remove triângulos do super-triângulo
        self.triangulation = {tri for tri in self.triangulation if not any(v in super_vertices for v in tri.vertices)}
        if verbose:
            print(f"\n\n[PASSO 3] Removidos triângulos associados ao super-triângulo.")
            print(f"Triangulação de Delaunay final com {len(self.triangulation)} triângulos.")

    def _create_super_triangle(self, verbose):
        min_x = min(p.x for p in self.points)
        max_x = max(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_y = max(p.y for p in self.points)

        dx = max_x - min_x
        dy = max_y - min_y
        delta_max = max(dx, dy)
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        v1 = Point(mid_x - 2 * delta_max, mid_y - delta_max)
        v2 = Point(mid_x + 2 * delta_max, mid_y - delta_max)
        v3 = Point(mid_x, mid_y + 2 * delta_max)
        
        if verbose:
            print("--- [PASSO 1a] Cálculo do Super-Triângulo ---")
            print(f"  Limites dos pontos: X=[{min_x:.2f}, {max_x:.2f}], Y=[{min_y:.2f}, {max_y:.2f}]")
            print(f"  Delta X={dx:.2f}, Delta Y={dy:.2f}, Delta Max={delta_max:.2f}")
            print(f"  Ponto Médio=({mid_x:.2f}, {mid_y:.2f})")
            print(f"  Vértice 1: ({mid_x:.2f} - 2*{delta_max:.2f}, {mid_y:.2f} - {delta_max:.2f}) = {v1}")
            print(f"  Vértice 2: ({mid_x:.2f} + 2*{delta_max:.2f}, {mid_y:.2f} - {delta_max:.2f}) = {v2}")
            print(f"  Vértice 3: ({mid_x:.2f}, {mid_y:.2f} + 2*{delta_max:.2f}) = {v3}")

        return (v1, v2, v3), {v1, v2, v3}

if __name__ == "__main__":
    # Use um número pequeno de pontos para um output legível
    NUM_SITES = 4
    random.seed(42)
    points = [[random.uniform(0, 100), random.uniform(0, 100)] for _ in range(NUM_SITES)]

    print(f"Pontos de entrada ({NUM_SITES}):")
    for p in points:
        print(f"  - ({p[0]:.2f}, {p[1]:.2f})")

    # Executa o algoritmo com a saída detalhada ativada
    bw_detailed = BowyerWatsonDetailed(points)
    bw_detailed.run(verbose=True)

    print("\n--- FIM DA EXECUÇÃO ---")
    print("A saída acima mostrou cada cálculo matemático realizado pelo algoritmo.")
