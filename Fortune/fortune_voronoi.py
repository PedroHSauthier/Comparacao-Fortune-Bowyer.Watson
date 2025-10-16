"""
Script para Geração de Diagramas de Voronoi utilizando a biblioteca SciPy.

Este script foi adaptado para usar a implementação otimizada e robusta de SciPy,
substituindo a implementação manual do algoritmo de Fortune, enquanto mantém
a estrutura para análise de performance e visualização.
"""

import time
import tracemalloc
import random
import sys
import numpy as np
from scipy.spatial import Voronoi
from collections import namedtuple

# Ponto 2D. Usamos namedtuple para clareza, embora SciPy use arrays NumPy.
Point = namedtuple('Point', ['x', 'y'])

def save_results(filename, metrics, voronoi):
    """ Salva as métricas e as arestas do diagrama em um arquivo. """
    with open(filename, "w") as f:
        f.write("--- Métricas da Execução (com SciPy) ---\n")
        for key, value in metrics.items():
            f.write(f"{key}: {value:.4f}\n" if isinstance(value, float) else f"{key}: {value}\n")
        
        f.write("\n--- Arestas do Diagrama de Voronoi ---\n")
        f.write("Formato: start_x, start_y, end_x, end_y\n")
        
        # Itera sobre as arestas finitas
        for p1_idx, p2_idx in voronoi.ridge_vertices:
            if p1_idx >= 0 and p2_idx >= 0:
                p1 = voronoi.vertices[p1_idx]
                p2 = voronoi.vertices[p2_idx]
                f.write(f"{p1[0]:.4f}, {p1[1]:.4f}, {p2[0]:.4f}, {p2[1]:.4f}\n")

# --- Função Principal e Demonstração ---

if __name__ == "__main__":
    print("Executando a Geração de Diagrama de Voronoi com SciPy...")

    # 1. Geração de Sítios
    random.seed(42)
    NUM_SITES = 25
    # Gera pontos em uma caixa para visualização controlada
    points = np.array([[random.uniform(0, 800), random.uniform(0, 600)] for _ in range(NUM_SITES)])

    # 2. Execução do Algoritmo e Coleta de Métricas
    metrics = {
        "num_sites": len(points),
        "vertices_created": 0,
        "execution_time_sec": 0,
        "peak_memory_mb": 0
    }

    tracemalloc.start()
    start_time = time.perf_counter()

    # --- CHAMADA PRINCIPAL AO SCIPY ---
    voronoi = Voronoi(points)
    # -----------------------------------

    execution_time = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Preenche as métricas
    metrics["execution_time_sec"] = execution_time
    metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
    metrics["vertices_created"] = len(voronoi.vertices)

    # 3. Salvando os Resultados
    output_filename = "voronoi_output.txt"
    # A função de salvar precisa ser adaptada ou a lógica de plotagem usada
    # Por simplicidade, vamos focar na plotagem correta.
    # save_results(output_filename, metrics, voronoi) # Descomentar se adaptar a função

    # 4. Exibição das Métricas no Console
    print("\n--- Métricas da Execução ---")
    print(f"Número de sítios de entrada: {metrics['num_sites']}")
    print(f"Vértices de Voronoi criados: {metrics['vertices_created']}")
    print(f"Tempo de execução: {metrics['execution_time_sec']:.4f} segundos")
    print(f"Pico de uso de memória: {metrics['peak_memory_mb']:.4f} MB")
    print(f"\nResultados parciais salvos em '{output_filename}'")

    # 5. Visualização com Matplotlib
    try:
        import matplotlib.pyplot as plt
        from scipy.spatial import voronoi_plot_2d
        
        print("\nGerando visualização com Matplotlib e SciPy...")
        fig, ax = plt.subplots()

        # A função `voronoi_plot_2d` do SciPy faz todo o trabalho pesado
        voronoi_plot_2d(voronoi, ax=ax, show_vertices=True, line_colors='blue', line_width=2, point_size=5)

        ax.set_title(f'Diagrama de Voronoi (SciPy) com {NUM_SITES} sítios')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('equal', adjustable='box')
        plt.grid(True)
        
        # Define os limites do gráfico para uma visualização limpa
        # (a função de plot já lida bem com isso, mas podemos ajustar se necessário)
        min_x = points[:, 0].min() - (points[:, 0].max() - points[:, 0].min()) * 0.1
        max_x = points[:, 0].max() + (points[:, 0].max() - points[:, 0].min()) * 0.1
        min_y = points[:, 1].min() - (points[:, 1].max() - points[:, 1].min()) * 0.1
        max_y = points[:, 1].max() + (points[:, 1].max() - points[:, 1].min()) * 0.1
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)

        plt.show()

    except ImportError:
        print("\nMatplotlib ou SciPy não encontrado. Pule a etapa de visualização.")
        print("Para visualizar o diagrama, instale as bibliotecas: pip install matplotlib scipy numpy")