# run_cython.py

import time
import random
import numpy as np
import matplotlib.pyplot as plt
from bowyer_watson_cython import BowyerWatsonCython # Import the compiled module

if __name__ == "__main__":
    print("Executando o Algoritmo de Bowyer-Watson (Versão Cython) para Diagrama de Voronoi...")

    # 1. Geração de Sítios
    random.seed(42)
    NUM_SITES = 500
    points = np.array([[random.uniform(0, 800), random.uniform(0, 600)] for _ in range(NUM_SITES)])

    # 2. Execução do Algoritmo
    start_time = time.perf_counter()
    bw_generator = BowyerWatsonCython(points)
    bw_generator.run()
    end_time = time.perf_counter()

    # 3. Exibição das Métricas
    print("\n--- Métricas da Execução (Cython) ---")
    print(f"Tempo de execução: {end_time - start_time:.4f} segundos")
    metrics = bw_generator.metrics
    for key, value in metrics.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value}")

    # 4. Visualização com Matplotlib
    print("\nGerando visualização com Matplotlib...")
    fig, ax = plt.subplots()
    
    # Plota os sítios
    ax.plot(points[:, 0], points[:, 1], 'o', color='red', label='Sítios')

    # Plota as arestas do diagrama de Voronoi
    voronoi_edges_plot = []
    for p1, p2 in bw_generator.voronoi_edges:
        voronoi_edges_plot.append(([p1.x, p2.x], [p1.y, p2.y]))

    for x_vals, y_vals in voronoi_edges_plot:
        ax.plot(x_vals, y_vals, 'b-')

    ax.set_title(f'Diagrama de Voronoi (Bowyer-Watson - Cython) com {NUM_SITES} sítios')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal', adjustable='box')
    ax.legend()
    plt.grid(True)
    
    min_x, max_x = points[:, 0].min(), points[:, 0].max()
    min_y, max_y = points[:, 1].min(), points[:, 1].max()
    dx = (max_x - min_x) * 0.1
    dy = (max_y - min_y) * 0.1
    ax.set_xlim(min_x - dx, max_x + dx)
    ax.set_ylim(min_y - dy, max_y + dy)

    plt.show()
