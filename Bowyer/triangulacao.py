"""
Visualizador Interativo do Algoritmo de Bowyer-Watson para Apresentações.

Use a BARRA DE ESPAÇO para avançar para o próximo passo do algoritmo.
Use a tecla ESC para fechar a janela.

O painel direito mostra os cálculos matemáticos detalhados para a etapa atual.
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
POINT_COLOR = (255, 0, 0)
TRIANGLE_COLOR = (100, 100, 100)
HIGHLIGHT_COLOR = (0, 150, 255)
BAD_TRIANGLE_COLOR = (255, 100, 100)
BOUNDARY_COLOR = (0, 200, 0)
FONT_SIZE = 20
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
        # 1. Super-triângulo
        super_triangle_verts, super_v_set = self._create_super_triangle()
        st = Triangle(*super_triangle_verts)
        self.triangulation.add(st)
        
        log = [
            "--- PASSO 1: Criar Super-Triângulo ---",
            f"Um triângulo que engloba todos os pontos.",
            f"Vértices: ",
            f"  V1: ({super_triangle_verts[0].x:.1f}, {super_triangle_verts[0].y:.1f})",
            f"  V2: ({super_triangle_verts[1].x:.1f}, {super_triangle_verts[1].y:.1f})",
            f"  V3: ({super_triangle_verts[2].x:.1f}, {super_triangle_verts[2].y:.1f})",
        ]
        yield self._create_frame(status="Início", log_text=log)

        # 2. Adicionar pontos incrementalmente
        for i, point in enumerate(self.points):
            bad_triangles = set()
            
            log = [f"--- PASSO 2.{i+1}: Adicionando Ponto ---", f"Ponto P = ({point.x:.1f}, {point.y:.1f})"]
            yield self._create_frame(status=f"Adicionando Ponto {i+1}", active_point=point, log_text=log)

            # Encontra triângulos "ruins"
            log = ["--- Verificando quais triângulos são 'ruins' ---", 
                   "Um triângulo é 'ruim' se o ponto P está dentro do seu circuncírculo."]
            yield self._create_frame(status="Encontrando triângulos ruins", active_point=point, log_text=log)

            temp_log = []
            for t in self.triangulation:
                dist_sq = (point.x - t.circumcenter.x)**2 + (point.y - t.circumcenter.y)**2
                is_bad = dist_sq < t.circumradius_sq
                
                calc_log = [
                    f"Triângulo T = {[(v.x, v.y) for v in t.vertices]}",
                    f"  Circuncentro C = ({t.circumcenter.x:.1f}, {t.circumcenter.y:.1f})",
                    f"  Raio^2 = {t.circumradius_sq:.1f}",
                    f"  Dist(P, C)^2 = ({point.x:.1f} - {t.circumcenter.x:.1f})^2 + ({point.y:.1f} - {t.circumcenter.y:.1f})^2 = {dist_sq:.1f}",
                    f"  Teste: {dist_sq:.1f} < {t.circumradius_sq:.1f} -> {'VERDADEIRO (Ruim)' if is_bad else 'FALSO'}",
                    ""
                ]
                temp_log.extend(calc_log)
                
                if is_bad:
                    bad_triangles.add(t)
                
                yield self._create_frame(
                    status="Verificando circuncírculos",
                    active_point=point,
                    bad_triangles=bad_triangles,
                    highlight_triangles={t},
                    log_text=log + temp_log
                )

            log = [f"--- {len(bad_triangles)} Triângulos Ruins Encontrados ---"]
            yield self._create_frame(status="Triângulos ruins identificados", active_point=point, bad_triangles=bad_triangles, log_text=log)

            # Encontra a borda do polígono
            polygon_boundary = set()
            for t in bad_triangles:
                for j in range(3):
                    v1, v2 = t.vertices[j], t.vertices[(j + 1) % 3]
                    edge = Edge(*tuple(sorted((v1, v2))))
                    if edge in polygon_boundary: polygon_boundary.remove(edge)
                    else: polygon_boundary.add(edge)
            
            log = ["--- Encontrando a Borda do 'Buraco' ---",
                   "Arestas que pertencem a apenas um triângulo ruim formam a borda."]
            yield self._create_frame(status="Formando o polígono", active_point=point, bad_triangles=bad_triangles, polygon_boundary=polygon_boundary, log_text=log)

            # Remove triângulos ruins
            self.triangulation -= bad_triangles
            log = ["--- Removendo Triângulos Ruins ---"]
            yield self._create_frame(status="Removendo triângulos", active_point=point, polygon_boundary=polygon_boundary, log_text=log)

            # Retriangula
            log = ["--- Preenchendo o 'Buraco' ---", "Criando novos triângulos a partir da borda e do ponto P."]
            new_triangles = set()
            for edge in polygon_boundary:
                new_triangle = Triangle(edge.v1, edge.v2, point)
                new_triangles.add(new_triangle)
            
            self.triangulation.update(new_triangles)
            yield self._create_frame(status="Retriangulando", active_point=point, polygon_boundary=polygon_boundary, highlight_triangles=new_triangles, log_text=log)

        # 3. Limpeza final
        self.triangulation = {t for t in self.triangulation if not any(v in super_v_set for v in t.vertices)}
        log = ["--- PASSO 3: Limpeza Final ---", "Removendo todos os triângulos que compartilham vértices com o super-triângulo inicial."]
        yield self._create_frame(status="Limpando super-triângulo", log_text=log)
        
        log = ["--- ALGORITMO CONCLUÍDO ---", f"Triangulação de Delaunay final com {len(self.triangulation)} triângulos."]
        yield self._create_frame(status="Concluído!", log_text=log)

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

    def _create_frame(self, status="", active_point=None, bad_triangles=None, polygon_boundary=None, highlight_triangles=None, log_text=None):
        return {
            "triangulation": self.triangulation.copy(),
            "points": self.points,
            "status": status,
            "active_point": active_point,
            "bad_triangles": bad_triangles or set(),
            "polygon_boundary": polygon_boundary or set(),
            "highlight_triangles": highlight_triangles or set(),
            "log_text": log_text or [],
        }

# --- Classe Principal da Visualização (Pygame) ---
class Visualizer:
    def __init__(self, points):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Visualizador Bowyer-Watson | Pressione ESPAÇO para avançar")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", FONT_SIZE)
        self.status_font = pygame.font.SysFont("Arial", STATUS_FONT_SIZE, bold=True)
        
        self.points = points
        self.bw_generator = BowyerWatsonVisualizer(points).run()
        self.current_frame = next(self.bw_generator)
        self.running = True
        self.paused = True

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(30)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                try:
                    self.current_frame = next(self.bw_generator)
                except StopIteration:
                    print("Algoritmo concluído.")

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_viz_panel()
        self.draw_text_panel()
        pygame.display.flip()

    def draw_viz_panel(self):
        frame = self.current_frame
        # Desenha triângulos normais
        for t in frame["triangulation"]:
            pygame.draw.polygon(self.screen, TRIANGLE_COLOR, [t.vertices[0], t.vertices[1], t.vertices[2]], 1)

        # Desenha triângulos ruins e seus circuncírculos
        for t in frame["bad_triangles"]:
            pygame.draw.polygon(self.screen, BAD_TRIANGLE_COLOR, [t.vertices[0], t.vertices[1], t.vertices[2]], 2)
            if t.circumcenter:
                pygame.draw.circle(self.screen, BAD_TRIANGLE_COLOR, (int(t.circumcenter.x), int(t.circumcenter.y)), int(math.sqrt(t.circumradius_sq)), 1)
        
        # Desenha triângulos destacados (sendo verificados ou recém-criados)
        for t in frame["highlight_triangles"]:
            pygame.draw.polygon(self.screen, HIGHLIGHT_COLOR, [t.vertices[0], t.vertices[1], t.vertices[2]], 3)
            if t.circumcenter:
                 pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (int(t.circumcenter.x), int(t.circumcenter.y)), int(math.sqrt(t.circumradius_sq)), 1)

        # Desenha a borda do polígono
        for edge in frame["polygon_boundary"]:
            pygame.draw.line(self.screen, BOUNDARY_COLOR, edge.v1, edge.v2, 3)

        # Desenha os pontos
        for p in frame["points"]:
            pygame.draw.circle(self.screen, POINT_COLOR, (int(p.x), int(p.y)), 5)
        
        # Desenha o ponto ativo
        if frame["active_point"]:
            pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (int(frame["active_point"].x), int(frame["active_point"].y)), 8)

    def draw_text_panel(self):
        panel_x = VIZ_PANEL_WIDTH
        pygame.draw.rect(self.screen, (220, 220, 220), (panel_x, 0, TEXT_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (180, 180, 180), (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

        # Título do Status
        status_surface = self.status_font.render(self.current_frame["status"], True, TEXT_COLOR)
        self.screen.blit(status_surface, (panel_x + 20, 20))

        # Log de cálculos
        y_offset = 80
        for i, line in enumerate(self.current_frame["log_text"]):
            line_surface = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(line_surface, (panel_x + 20, y_offset + i * (FONT_SIZE + 5)))

if __name__ == "__main__":
    # Use um número pequeno de pontos para uma apresentação clara
    NUM_SITES = 8
    random.seed(42) 
    # Garante que os pontos fiquem bem distribuídos e longe das bordas
    points = [[random.uniform(100, VIZ_PANEL_WIDTH - 100), random.uniform(100, SCREEN_HEIGHT - 100)] for _ in range(NUM_SITES)]

    app = Visualizer(points)
    app.run()
