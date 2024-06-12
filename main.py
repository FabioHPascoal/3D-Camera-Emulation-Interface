import sys
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QLabel, QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton,QGroupBox
from PyQt5.QtGui import QDoubleValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh
from mpl_toolkits.mplot3d import art3d
from math import pi,cos,sin

def translation(dx,dy,dz):
    t = np.array([dx,dy,dz,1])
    T = np.eye(4)
    T[:,-1]=t.T
    return T

def rotate_x(angle):
    angle = np.radians(angle)
    rotation_matrix=np.array([[1,0,0,0],[0, cos(angle),-sin(angle),0],[0, sin(angle), cos(angle),0],[0,0,0,1]])
    return rotation_matrix

def rotate_y(angle):
    angle = np.radians(angle)
    rotation_matrix=np.array([[cos(angle),0, sin(angle),0],[0,1,0,0],[-sin(angle), 0, cos(angle),0],[0,0,0,1]])
    return rotation_matrix

def rotate_z(angle):
    angle = np.radians(angle)
    rotation_matrix=np.array([[cos(angle),-sin(angle),0,0],[sin(angle),cos(angle),0,0],[0,0,1,0],[0,0,0,1]])
    return rotation_matrix
    
def draw_arrows(point, base, axes, length):
    # Plot x-axis vector
    x_quiver = axes.quiver(point[0],point[1],point[2],base[0,0],base[1,0],base[2,0],color='red',pivot='tail', length=length)
    # Plot y-axis vector
    y_quiver = axes.quiver(point[0],point[1],point[2],base[0,1],base[1,1],base[2,1],color='green',pivot='tail', length=length)
    # Plot z-axis vector
    z_quiver = axes.quiver(point[0],point[1],point[2],base[0,2],base[1,2],base[2,2],color='blue',pivot='tail', length=length)

    return x_quiver, y_quiver, z_quiver

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resol_changed = False
        #definindo as variaveis
        self.constants()
        self.set_variables()
        #Ajustando a tela    
        self.setWindowTitle("Grid Layout")
        self.setGeometry(100, 100, 1280, 720)
        self.setup_ui()

    def set_variables(self):
        self.cam_original = np.array([[1, 0, 0, 0], [0, 0, 1, -50], [0, -1, 0, 40], [0, 0, 0, 1]])
        # self.cam_original = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.cam = self.cam_original
        self.px_base = 1280
        self.px_altura = 720
        self.dist_foc = 10
        self.stheta = 0
        self.ox = self.px_base/2
        self.oy = self.px_altura/2
        self.ccd = [36, 24]
        self.projection_matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])

    def constants(self):

        e1 = np.array([[1],[0],[0],[0]]) # X
        e2 = np.array([[0],[1],[0],[0]]) # Y
        e3 = np.array([[0],[0],[1],[0]]) # Z
        self.base = np.hstack((e1, e2, e3)) # Cartesian base
        self.point = np.array([[0],[0],[0],[1]]) # Origin
        
    def setup_ui(self):
        # Criar o layout de grade
        grid_layout = QGridLayout()

        # Criar os widgets
        line_edit_widget1 = self.create_world_widget("Ref mundo")
        line_edit_widget2 = self.create_cam_widget("Ref camera")
        line_edit_widget3 = self.create_intrinsic_widget("params instr")

        self.canvas = self.create_matplotlib_canvas()

        # Adicionar os widgets ao layout de grade
        grid_layout.addWidget(line_edit_widget1, 0, 0)
        grid_layout.addWidget(line_edit_widget2, 0, 1)
        grid_layout.addWidget(line_edit_widget3, 0, 2)
        grid_layout.addWidget(self.canvas, 1, 0, 1, 3)

        # Criar um widget para agrupar o botão de reset
        reset_widget = QWidget()
        reset_layout = QHBoxLayout()
        reset_widget.setLayout(reset_layout)

        # Criar o botão de reset vermelho
        reset_button = QPushButton("Reset")
        reset_button.setFixedSize(50, 30)  # Define um tamanho fixo para o botão (largura: 50 pixels, altura: 30 pixels)
        style_sheet = """
            QPushButton {
                color : white ;
                background: rgba(255, 50, 50, 210);
                font: inherit;
                border-radius: 5px;
                line-height: 1;
            }
        """
        reset_button.setStyleSheet(style_sheet)
        reset_button.clicked.connect(self.reset_canvas)

        # Adicionar o botão de reset ao layout
        reset_layout.addWidget(reset_button)

        # Adicionar o widget de reset ao layout de grade
        grid_layout.addWidget(reset_widget, 2, 0, 1, 3)

        # Criar um widget central e definir o layout de grade como seu layout
        central_widget = QWidget()
        central_widget.setLayout(grid_layout)
        
        # Definir o widget central na janela principal
        self.setCentralWidget(central_widget)

    def create_intrinsic_widget(self, title):
        # Criar um widget para agrupar os QLineEdit
        line_edit_widget = QGroupBox(title)
        line_edit_layout = QVBoxLayout()
        line_edit_widget.setLayout(line_edit_layout)

        # Criar um layout de grade para dividir os QLineEdit em 3 colunas
        grid_layout = QGridLayout()

        line_edits = []
        labels = ['n_pixels_base:', 'n_pixels_altura:', 'ccd_x:', 'ccd_y:', 'dist_focal:', 'sθ:']  # Texto a ser exibido antes de cada QLineEdit

        # Adicionar widgets QLineEdit com caixa de texto ao layout de grade
        for i in range(1, 7):
            line_edit = QLineEdit()
            label = QLabel(labels[i-1])
            validator = QDoubleValidator()  # Validador numérico
            line_edit.setValidator(validator)  # Aplicar o validador ao QLineEdit
            grid_layout.addWidget(label, (i-1)//2, 2*((i-1)%2))
            grid_layout.addWidget(line_edit, (i-1)//2, 2*((i-1)%2) + 1)
            line_edits.append(line_edit)

        # Criar o botão de atualização
        update_button = QPushButton("Atualizar")

        ##### Você deverá criar, no espaço reservado ao final, a função self.update_params_intrinsc ou outra que você queira 
        # Conectar a função de atualização aos sinais de clique do botão
        update_button.clicked.connect(lambda: self.update_params_intrinsc(line_edits))

        # Adicionar os widgets ao layout do widget line_edit_widget
        line_edit_layout.addLayout(grid_layout)
        line_edit_layout.addWidget(update_button)

        # Retornar o widget e a lista de caixas de texto
        return line_edit_widget
    
    def create_world_widget(self, title):
        # Criar um widget para agrupar os QLineEdit
        line_edit_widget = QGroupBox(title)
        line_edit_layout = QVBoxLayout()
        line_edit_widget.setLayout(line_edit_layout)

        # Criar um layout de grade para dividir os QLineEdit em 3 colunas
        grid_layout = QGridLayout()

        line_edits = []
        labels = ['X(move):', 'X(angle):', 'Y(move):', 'Y(angle):', 'Z(move):', 'Z(angle):']  # Texto a ser exibido antes de cada QLineEdit

        # Adicionar widgets QLineEdit com caixa de texto ao layout de grade
        for i in range(1, 7):
            line_edit = QLineEdit()
            label = QLabel(labels[i-1])
            validator = QDoubleValidator()  # Validador numérico
            line_edit.setValidator(validator)  # Aplicar o validador ao QLineEdit
            grid_layout.addWidget(label, (i-1)//2, 2*((i-1)%2))
            grid_layout.addWidget(line_edit, (i-1)//2, 2*((i-1)%2) + 1)
            line_edits.append(line_edit)

        # Criar o botão de atualização
        update_button = QPushButton("Atualizar")

        ##### Você deverá criar, no espaço reservado ao final, a função self.update_world ou outra que você queira 
        # Conectar a função de atualização aos sinais de clique do botão
        update_button.clicked.connect(lambda: self.update_world(line_edits))

        # Adicionar os widgets ao layout do widget line_edit_widget
        line_edit_layout.addLayout(grid_layout)
        line_edit_layout.addWidget(update_button)

        # Retornar o widget e a lista de caixas de texto
        return line_edit_widget

    def create_cam_widget(self, title):
        # Criar um widget para agrupar os QLineEdit
        line_edit_widget = QGroupBox(title)
        line_edit_layout = QVBoxLayout()
        line_edit_widget.setLayout(line_edit_layout)

        # Criar um layout de grade para dividir os QLineEdit em 3 colunas
        grid_layout = QGridLayout()

        line_edits = []
        labels = ['X(move):', 'X(angle):', 'Y(move):', 'Y(angle):', 'Z(move):', 'Z(angle):']  # Texto a ser exibido antes de cada QLineEdit

        # Adicionar widgets QLineEdit com caixa de texto ao layout de grade
        for i in range(1, 7):
            line_edit = QLineEdit()
            label = QLabel(labels[i-1])
            validator = QDoubleValidator()  # Validador numérico
            line_edit.setValidator(validator)  # Aplicar o validador ao QLineEdit
            grid_layout.addWidget(label, (i-1)//2, 2*((i-1)%2))
            grid_layout.addWidget(line_edit, (i-1)//2, 2*((i-1)%2) + 1)
            line_edits.append(line_edit)

        # Criar o botão de atualização
        update_button = QPushButton("Atualizar")

        ##### Você deverá criar, no espaço reservado ao final, a função self.update_cam ou outra que você queira 
        # Conectar a função de atualização aos sinais de clique do botão
        update_button.clicked.connect(lambda: self.update_cam(line_edits))

        # Adicionar os widgets ao layout do widget line_edit_widget
        line_edit_layout.addLayout(grid_layout)
        line_edit_layout.addWidget(update_button)

        # Retornar o widget e a lista de caixas de texto
        return line_edit_widget

    def create_matplotlib_canvas(self):
        
        # Criar um widget para exibir os gráficos do Matplotlib
        canvas_widget = QWidget()
        canvas_layout = QHBoxLayout()
        canvas_widget.setLayout(canvas_layout)

        # Criar um objeto FigureCanvas para exibir o gráfico 2D
        self.fig1, self.ax1 = plt.subplots()
        self.ax1.set_title("Imagem")
        self.canvas1 = FigureCanvas(self.fig1)

        ##### Falta acertar os limites do eixo X
        self.ax1.set_xlim(self.ox - self.px_base/2, self.ox + self.px_base/2)
        self.ax1.xaxis.tick_top()
        
        ##### Falta acertar os limites do eixo Y
        self.ax1.set_ylim(self.oy + self.px_altura/2, self.oy - self.px_altura/2)

        # Opening STL file
        your_mesh = mesh.Mesh.from_file('link.STL')
        
        # Get the x, y, z coordinates contained in the mesh structure that are the
        # vertices of the triangular faces of the object
        x = your_mesh.x.flatten()
        y = your_mesh.y.flatten()
        z = your_mesh.z.flatten()

        # Get the vectors that define the triangular faces that form the 3D object
        obj_vectors = your_mesh.vectors

        # Create the 3D object from the x,y,z coordinates and add the additional array of ones to
        # represent the object using homogeneous coordinates
        self.obj = np.array([x.T, y.T, z.T, np.ones(x.size)]) 

        ##### Você deverá criar a função de projeção 
        obj_2d = self.projection_2d()

        ##### Falta plotar o object_2d que retornou da projeção
        self.obj_projected = self.ax1.plot(obj_2d[0, :], obj_2d[1, :], color = (0.2, 0.2, 0.2, 0.9), linewidth = 0.3) 
        
        self.ax1.grid('True')
        self.ax1.set_aspect('equal')  
        canvas_layout.addWidget(self.canvas1)

        # Criar um objeto FigureCanvas para exibir o gráfico 3D
        self.fig2 = plt.figure()
        self.ax2 = self.fig2.add_subplot(111, projection = '3d')

        # Turning on interactive mode
        plt.ion()

        # Set axes and their aspect
        self.ax2.auto_scale_xyz(self.obj[0, :], self.obj[1, :], self.obj[2, :])

        x_limits = self.ax2.get_xlim3d()
        y_limits = self.ax2.get_ylim3d()
        z_limits = self.ax2.get_zlim3d()

        x_range = abs(x_limits[1] - x_limits[0])*1.2
        x_middle = np.mean(x_limits)
        y_range = abs(y_limits[1] - y_limits[0])*1.2
        y_middle = np.mean(y_limits)
        z_range = abs(z_limits[1] - z_limits[0])*1.2
        z_middle = np.mean(z_limits)

        # The plot bounding box is a sphere in the sense of the infinity
        # norm, hence I call half the max range the plot radius.
        plot_radius = 0.5 * max([x_range, y_range, z_range])

        self.ax2.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
        self.ax2.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
        self.ax2.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

        self.ax2.view_init(elev = 30, azim = -45)
        self.ax2.set_box_aspect(None, zoom = 1.2)

        # Plot and render the faces of the object
        collection = art3d.Poly3DCollection(obj_vectors, linewidths = 1, alpha = 0.2)
        face_color = (0.4, 0.4, 0.4, 0.1)
        collection.set_facecolor(face_color)
        self.ax2.add_collection3d(collection)

        # Plot the contours of the faces of the object
        self.ax2.add_collection3d(art3d.Line3DCollection(obj_vectors, colors = 'k', linewidths = 0.2, linestyles = '-'))
     
        # Referencial do mundo
        draw_arrows(self.point, self.base, self.ax2, 15)
       
        # Referencial da camera
        self.x_quiver, self.y_quiver, self.z_quiver = draw_arrows((self.cam.T)[3], np.delete(self.cam, 3, 1), self.ax2, 10)

        self.canvas2 = FigureCanvas(self.fig2)
        canvas_layout.addWidget(self.canvas2)

        # Retornar o widget de canvas
        return canvas_widget
    
    def update_params_intrinsc(self, line_edits):

        i = 0
        self.resol_changed = False
        for obj in line_edits:
            if obj.text().isnumeric():
                if i == 0: 
                    self.px_base = float(obj.text())
                    self.resol_changed = True
                elif i == 1: 
                    self.px_altura = float(obj.text())
                    self.resol_changed = True
                elif i == 2: self.ccd[0] = float(obj.text())
                elif i == 3: self.ccd[1] = float(obj.text())
                elif i == 4: self.dist_foc = float(obj.text())
                elif i == 5: self.stheta = float(obj.text())
            i = i+1

        # Canvas Update
        self.update_canvas()

        return None 

    def update_world(self, line_edits):

        changes = []
        for obj in line_edits:
            if obj.text() == '':
                changes.append(0)
            else:
                changes.append(float((obj.text())))
        
        # Translations
        self.cam = translation(changes[0], changes[2], changes[4]) @ self.cam

        # Rotations (x -> y -> z)
        self.cam = rotate_x(changes[1]) @ self.cam
        self.cam = rotate_y(changes[3]) @ self.cam
        self.cam = rotate_z(changes[5]) @ self.cam

        # Canvas Update
        self.update_canvas()

        return None

    def update_cam(self, line_edits):
    
        changes = []
        for obj in line_edits:
            if obj.text() == '':
                changes.append(0)
            else:
                changes.append(float((obj.text())))

        # Translations
        self.cam = self.cam @ translation(changes[0], changes[2], changes[4])
        
        # Rotations (x -> y -> z)
        self.cam = self.cam @ rotate_x(changes[1])
        self.cam = self.cam @ rotate_y(changes[3])
        self.cam = self.cam @ rotate_z(changes[5])

        # Canvas Update
        self.update_canvas()

        return None
    
    def projection_2d(self):
        self.generate_intrinsic_params_matrix()

        # print(self.obj.shape)
        lambda_obj_2d = self.intrinsic_params_matrix @ self.projection_matrix @ np.linalg.inv(self.cam) @ self.obj

        zeros = np.flip(np.where(lambda_obj_2d == 0)[1])
        for i in range(len(zeros)):
            lambda_obj_2d = np.delete(lambda_obj_2d, zeros[i], 1)

        obj_2d = lambda_obj_2d[:2, :] / lambda_obj_2d[2, :]

        # print(self.cam)
        # print("\n")
        
        return obj_2d
    
    def generate_intrinsic_params_matrix(self):
        f_x = (self.px_base/self.ccd[0]) * self.dist_foc
        f_y = (self.px_altura/self.ccd[1]) * self.dist_foc
        f_theta = self.stheta * self.dist_foc
        ox = self.ox
        oy = self.oy

        self.intrinsic_params_matrix = np.array([[f_x, f_theta, ox], [0, f_y, oy], [0, 0, 1]])

        return None

    def update_canvas(self):

        if self.resol_changed:
            self.ox = self.px_base/2
            self.oy = self.px_altura/2
            
            # Updating X limits
            self.ax1.set_xlim(self.ox - self.px_base/2, self.ox + self.px_base/2)
            self.ax1.xaxis.tick_top()
            
            # Updating Y limits
            self.ax1.set_ylim(self.oy + self.px_altura/2, self.oy - self.px_altura/2)
     
        # Axes 1
        for point in self.obj_projected:
            point.remove()

        obj_2d = self.projection_2d()
        self.obj_projected = self.ax1.plot(obj_2d[0, :], obj_2d[1, :], color = (0.2, 0.2, 0.2, 0.9), linewidth = 0.3)

        # Axes 2
        self.x_quiver.remove()
        self.y_quiver.remove()
        self.z_quiver.remove()

        self.x_quiver, self.y_quiver, self.z_quiver = draw_arrows(self.cam[:,3], self.cam[:,0:3], self.ax2, 10)

        return None
    
    def reset_canvas(self):
        self.cam = self.cam_original

        # Canvas Update
        self.update_canvas()        

        return None
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())