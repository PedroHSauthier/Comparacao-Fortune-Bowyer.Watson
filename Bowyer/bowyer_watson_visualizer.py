"""
Visualizador Interativo do Algoritmo de Bowyer-Watson e do Diagrama de Voronoi.

Use a BARRA DE ESPAÇO para avançar para o próximo passo do algoritmo.
Use a tecla ESC para fechar a janela.

Fases:
1. Construção da Triangulação de Delaunay.
2. Derivação do Diagrama de Voronoi a partir da triangulação.
"""
import pygame
import math
import random
from collections import namedtuple

# --- Configurações da Visualização ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1980, 1080
VIZ_PANEL_WIDTH = 1000
TEXT_PANEL_WIDTH = SCREEN_WIDTH - VIZ_PANEL_WIDTH
BACKGROUND_COLOR = (240, 240, 240)
TEXT_COLOR = (10, 10, 10)
POINT_COLOR = (255, 0, 0) # Sítios originais
# Cores Delaunay
TRIANGLE_COLOR = (100, 100, 100)
DELAUNAY_BG_COLOR = (200, 200, 200)
HIGHLIGHT_COLOR = (0, 150, 255)
BAD_TRIANGLE_COLOR = (255, 100, 100)
BOUNDARY_COLOR = (0, 200, 0)
# Cores Voronoi
VORONOI_VERTEX_COLOR = (0, 100, 0)
VORONOI_EDGE_COLOR = (0, 0, 200)

FONT_SIZE = 18
STATUS_FONT_SIZE = 24

# --- Estruturas de Dados Geométricas ---
Point = namedtuple('Point', ['x', 'y'])
Edge = namedtuple('Edge', ['v1', 'v2'])

class Triangle:
    def __init__(self, v1, v2, v3):
        self.vertices = tuple(sorted((v1, v2, v3)))
        self.circumcenter, self.circumradius_sq = self._calculate_circumcircle()

    def __eq__(self, other):
        return self.vertices == other.vertices
    def __hash__(self):
        return hash(self.vertices)

    def _calculate_circumcircle(self):
        p1, p2, p3 = self.vertices
        D = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))
        if abs(D) < 1e-10: return None, float('inf')
        p1_sq, p2_sq, p3_sq = p1.x**2 + p1.y**2, p2.x**2 + p2.y**2, p3.x**2 + p3.y**2
        ux = (p1_sq * (p2.y - p3.y) + p2_sq * (p3.y - p1.y) + p3_sq * (p1.y - p2.y)) / D
        uy = (p1_sq * (p3.x - p2.x) + p2_sq * (p1.x - p3.x) + p3_sq * (p2.x - p1.x)) / D
        center = Point(ux, uy)
        radius_sq = (p1.x - ux)**2 + (p1.y - uy)**2
        return center, radius_sq

    def point_in_circumcircle(self, point):
        if self.circumcenter is None: return False
        dist_sq = (point.x - self.circumcenter.x)**2 + (point.y - self.circumcenter.y)**2
        return dist_sq < self.circumradius_sq

# --- Lógica do Algoritmo como um Gerador ---
class BowyerWatsonVisualizer:
    def __init__(self, points):
        self.points = [Point(p[0], p[1]) for p in points]
        self.triangulation = set()

    def run(self):
        # Fases 1, 2 e 3: Construção da Triangulação de Delaunay (código anterior)
        super_triangle_verts, super_v_set = self._create_super_triangle()
        self.triangulation.add(Triangle(*super_triangle_verts))
        yield self._create_frame(status="Início", log_text=["PASSO 1: Criar Super-Triângulo"])

        for i, point in enumerate(self.points):
            # ... (código de adição de ponto, busca de triângulos ruins, etc.)
            # Esta parte é omitida por brevidade, mas é a mesma de antes.
            bad_triangles = {t for t in self.triangulation if t.point_in_circumcircle(point)}
            polygon_boundary = set()
            for t in bad_triangles:
                for j in range(3):
                    v1, v2 = t.vertices[j], t.vertices[(j + 1) % 3]
                    edge = Edge(*tuple(sorted((v1, v2))))
                    if edge in polygon_boundary: polygon_boundary.remove(edge)
                    else: polygon_boundary.add(edge)
            self.triangulation -= bad_triangles
            for edge in polygon_boundary:
                self.triangulation.add(Triangle(edge.v1, edge.v2, point))
        
        yield self._create_frame(status="Triangulação Quase Pronta", log_text=["Limpando..."])
        self.triangulation = {t for t in self.triangulation if not any(v in super_v_set for v in t.vertices)}
        log = ["--- Triangulação de Delaunay Concluída ---", f"{len(self.triangulation)} triângulos finais."]
        yield self._create_frame(status="Delaunay Concluído", log_text=log)

        # --- PASSO 4: Derivar Diagrama de Voronoi (Dual) ---
        log = ["--- PASSO 4: Gerando o Diagrama de Voronoi ---", "O Voronoi é o dual da Triangulação de Delaunay."]
        yield self._create_frame(status="Iniciando Geração Voronoi", log_text=log, delaunay_bg=True)

        # 4a. Encontrar Vértices de Voronoi (Circuncentros)
        voronoi_vertices = set()
        log = ["--- 4a: Vértices Voronoi = Circuncentros ---", "Cada vértice do Voronoi é o circuncentro de um triângulo de Delaunay."]
        yield self._create_frame(status="Encontrando Vértices Voronoi", log_text=log, delaunay_bg=True)

        for t in self.triangulation:
            if t.circumcenter:
                voronoi_vertices.add(t.circumcenter)
                log_step = [f"Triângulo T: ({t.vertices[0].x:.0f},{t.vertices[0].y:.0f}), ({t.vertices[1].x:.0f},{t.vertices[1].y:.0f}), ...",
                            f"  -> Vértice Voronoi V: ({t.circumcenter.x:.1f}, {t.circumcenter.y:.1f})"]
                yield self._create_frame(status="Mapeando Triângulo -> Vértice Voronoi", highlight_triangles={t}, voronoi_vertices=voronoi_vertices, log_text=log + log_step, delaunay_bg=True)

        # 4b. Encontrar Arestas de Voronoi
        edge_to_triangles = {}
        for t in self.triangulation:
            for i in range(3):
                edge = Edge(*tuple(sorted((t.vertices[i], t.vertices[(i + 1) % 3]))))
                if edge not in edge_to_triangles:
                    edge_to_triangles[edge] = []
                edge_to_triangles[edge].append(t)

        log = ["--- 4b: Arestas de Voronoi ---", "Conectam circuncentros de triângulos adjacentes."]
        yield self._create_frame(status="Encontrando Arestas Voronoi", voronoi_vertices=voronoi_vertices, log_text=log, delaunay_bg=True)

        voronoi_edges = set()
        for edge, triangles in edge_to_triangles.items():
            if len(triangles) == 2:
                t1, t2 = triangles
                if t1.circumcenter and t2.circumcenter:
                    voronoi_edges.add(Edge(t1.circumcenter, t2.circumcenter))
                    log_step = [f"Aresta Delaunay compartilhada",
                                f"  -> Conecta circuncentros de T1 e T2."]
                    yield self._create_frame(status="Conectando Vértices Voronoi", highlight_triangles={t1, t2}, voronoi_vertices=voronoi_vertices, voronoi_edges=voronoi_edges, log_text=log + log_step, delaunay_bg=True)

        # 5. Resultado Final
        log = ["--- Diagrama de Voronoi Concluído ---"]
        yield self._create_frame(status="Resultado Final: Voronoi", voronoi_vertices=voronoi_vertices, voronoi_edges=voronoi_edges, log_text=log)

    def _create_super_triangle(self):
        min_x, max_x = min(p.x for p in self.points), max(p.x for p in self.points)
        min_y, max_y = min(p.y for p in self.points), max(p.y for p in self.points)
        dx, dy = max_x - min_x, max_y - min_y
        delta_max = max(dx, dy)
        mid_x, mid_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        v1 = Point(mid_x - 2 * delta_max, mid_y - delta_max)
        v2 = Point(mid_x + 2 * delta_max, mid_y - delta_max)
        v3 = Point(mid_x, mid_y + 2 * delta_max)
        return (v1, v2, v3), {v1, v2, v3}

    def _create_frame(self, **kwargs):
        # Define um frame padrão e o atualiza com os argumentos passados
        frame = {
            "triangulation": self.triangulation.copy(), "points": self.points,
            "status": "", "active_point": None, "bad_triangles": set(),
            "polygon_boundary": set(), "highlight_triangles": set(), "log_text": [],
            "delaunay_bg": False, "voronoi_vertices": set(), "voronoi_edges": set()
        }
        frame.update(kwargs)
        return frame

# --- Classe Principal da Visualização (Pygame) ---
class Visualizer:
    def __init__(self, points):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Visualizador Bowyer-Watson & Voronoi | ESPAÇO para avançar")
        self.font = pygame.font.SysFont("Consolas", FONT_SIZE)
        self.status_font = pygame.font.SysFont("Arial", STATUS_FONT_SIZE, bold=True)
        self.bw_generator = BowyerWatsonVisualizer(points).run()
        self.current_frame = next(self.bw_generator)
        self.running = True

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.time.Clock().tick(30)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                try: self.current_frame = next(self.bw_generator)
                except StopIteration: print("Algoritmo concluído.")

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_viz_panel(self.current_frame)
        self.draw_text_panel(self.current_frame)
        pygame.display.flip()

    def draw_viz_panel(self, frame):
        # Desenha a triangulação (normal ou como fundo)
        tri_color = DELAUNAY_BG_COLOR if frame['delaunay_bg'] else TRIANGLE_COLOR
        for t in frame["triangulation"]:
            pygame.draw.polygon(self.screen, tri_color, [t.vertices[0], t.vertices[1], t.vertices[2]], 1)
        
        # Destaques da fase Delaunay
        for t in frame["highlight_triangles"]: pygame.draw.polygon(self.screen, HIGHLIGHT_COLOR, [v for v in t.vertices], 3)
        
        # Desenha os Sítios
        for p in frame["points"]: pygame.draw.circle(self.screen, POINT_COLOR, (int(p.x), int(p.y)), 5)

        # Desenha Vértices e Arestas de Voronoi
        for v in frame["voronoi_vertices"]: pygame.draw.circle(self.screen, VORONOI_VERTEX_COLOR, (int(v.x), int(v.y)), 6)
        for edge in frame["voronoi_edges"]: pygame.draw.line(self.screen, VORONOI_EDGE_COLOR, edge.v1, edge.v2, 2)

    def draw_text_panel(self, frame):
        panel_x = VIZ_PANEL_WIDTH
        pygame.draw.rect(self.screen, (220, 220, 220), (panel_x, 0, TEXT_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (180, 180, 180), (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)
        status_surface = self.status_font.render(frame["status"], True, TEXT_COLOR)
        self.screen.blit(status_surface, (panel_x + 20, 20))
        y_offset = 80
        for i, line in enumerate(frame["log_text"]):
            line_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(line_surface, (panel_x + 20, y_offset + i * (FONT_SIZE + 4)))

if __name__ == "__main__":
    NUM_SITES = 8
    random.seed(42)
    points = [[random.uniform(100, VIZ_PANEL_WIDTH - 100), random.uniform(100, SCREEN_HEIGHT - 100)] for _ in range(NUM_SITES)]
    Visualizer(points).run()