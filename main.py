import sys
import os
import subprocess
import shutil
import struct
import configparser
import locale
import fsb5

# PySide bindings
import PySide
from PySide.QtGui import *
from PySide.QtCore import *
from PySide.QtOpenGL import *
from PySide.QtMultimedia import *

from OpenGL.GL import *

import res_rc

langs = [
    "en_US",
    "ru_RU"
    ]

developers = [
    "aspadm",
    "volfin",
    "Sir Kane",
    "erik945",
    "Vindis",
    "Simon Pinfold"
    ]

version = "1.1 (17.09.2017)"

ext_preview = [
    "pc_weightedprim",
    "pc_tex",
    "pc_prim",
    "pc_linkedprim",
            ]

ext_non_preview = [
    "pc_hair",
    "pc_apex",
    "pc_swf",
    "pc_fsb"
            ]

all_types = [
    "pc_animation", "pc_animationrig", "pc_animset", "pc_apex", "pc_binkvid",
    "pc_bonerig", "pc_chartype", "pc_coll", "pc_collisionlayers",
    "pc_coverdata", "pc_curvetex", "pc_decalpreset", "pc_entityblueprint",
    "pc_entityresource", "pc_entitytemplate", "pc_entitytype", "pc_facefx",
    "pc_fontdef", "pc_fsb", "pc_fsbm", "pc_hair", "pc_ies", "pc_irv",
    "pc_kitsystem", "pc_linkedprim", "pc_localized-fontdef",
    "pc_localized-swf", "pc_localized-textlist", "pc_localized-wavebank",
    "pc_mate", "pc_mi", "pc_musiccomp", "pc_navmesh", "pc_platformspecific",
    "pc_prim", "pc_rawentityblueprint", "pc_rawentitytype", "pc_rbs",
    "pc_resourceidx", "pc_resourcelist", "pc_rigdataresource", "pc_rtet",
    "pc_sdefs", "pc_socialresource", "pc_staticvisibility", "pc_swf", "pc_tex",
    "pc_textline", "pc_textlist", "pc_umbra", "pc_volumetricnavgraph",
    "pc_wavebank", "pc_wavebankfx", "pc_weightedprim"
            ]

ext_types = []

if os.path.isfile("unpack_ext.txt"):
    for i in open("unpack_ext.txt", "r"):
        if len(i) > 0:
            if i[-1] == "\n":
                i = i[:-1]
            if i in all_types:
                ext_types.append(i)

if ext_types == []:
    ext_types = ext_preview[:] + ext_non_preview[:]

types_3d = [
    "prim",
    "weightedprim",
    "linkedprim",
    "staticscenecollisiondef",
    "apx"
            ]

types_tex = [
    "tex"
            ]

types_audio = [
    "wavebank"
            ]

save_filter = [
    "OBJ - Wavefront Object (*.obj);;\
FBX - Autodesc Filmbox (*.fbx);;\
3DS - 3D Studio Graphics (*.3ds);;\
STL - Stereolithography Interface Format (*.stl);;\
PRIM - DEMD native model (*.bin)",
    "PNG - Portable Network Graphics (*.png);;\
TGA - Targa bitmap (*.tga);;\
JPG - JPEG (*.jpg);;\
TIF - Tagged Image Format File (*.tif);;\
DDS - Direct Draw Surface (*.dds);;\
TXET - DEMD native texture (*.tex)"
            ]

save_ext_tex = [
    "png", "tga",
    "jpg", "tif",
    "dds", "tex"
            ]

save_ext_3d = [
    "obj", "fbx",
    "3ds", "stl",
    "bin"
            ]

tree_list = [] # List of files by levels
folder_tree = {} # Pairs of filename: dirname

path = ""
lpath = os.getcwd() + "\\"
tpath = lpath+"temp_files\\"
last_dir = ""
last_filter = ["", ""]

# Toolset
dds_converter = ""
tex_converter = ""
unpacker = ""
blender = ""

# Fast export
epath = ""
ext_textures = ""
ext_models = ""

# Current element
file_name = ""
file_parent = ""
cur_hash = ""
cur_item = QTreeWidgetItem()

lang_name = ""
first_launch = False

icons = {"prim": ":/3d.png",
         "tex": ":/tex.png",
         "platform-tex": ":/tex.png",
         "linkedprim": ":/3da.png",
         "weightedprim": ":/3db.png",
         "apx": ":/apx.png",
         "hair": ":/hair.png",
         "wavebank": ":/mus.png"}

#
##### 3D viewer class
class GLWidget(QGLWidget):
    def __init__(self, parent=None, shareWidget=None):
        super(GLWidget, self).__init__(parent, shareWidget)
        self.clearColor = Qt.white

        self.zoom_scale = 0.001 # wheel step
        self.angle = 15 # arrows angle step
        self.angle_scale = 1.0 # mouse rotation
        self.move_scale = 0.001 # mouse position
        self.size_scale = 0.02 # mouse scaling
        self.size_hint = 0.7 # avoid clipping

        # Model rotation
        self.xRot = -90
        self.yRot = 0
        self.zRot = 180

        # Model screen position and scale
        self.xOff =  0.0
        self.yOff = -0.5
        self.zOff =  0.9

        # Last mouse pos
        self.lastPos = QPoint()

        self.v_list = []
        self.n_list = []
        self.v_count = 0

        self.can_show = False

    def add_vertex(self, vertex):
        vertex[0][0] *= -1
        vertex[1][0] *= -1
        vertex[2][0] *= -1
        for i in range(3):
            for j in range(3):
                self.size_hint = max(self.size_hint, vertex[i][j])
        for v in vertex[2]:
            self.v_list.append(v)
        for v in vertex[1]:
            self.v_list.append(v)
        for v in vertex[0]:
            self.v_list.append(v)
        Ux = vertex[1][0] - vertex[2][0]
        Uy = vertex[1][1] - vertex[2][1]
        Uz = vertex[1][2] - vertex[2][2]
        Vx = vertex[0][0] - vertex[2][0]
        Vy = vertex[0][1] - vertex[2][1]
        Vz = vertex[0][2] - vertex[2][2]
        normal = [Uy*Vz - Uz*Vy, Uz*Vx - Ux*Vz, Ux*Vy - Uy*Vx]
        for k in range(3):
            for v in normal:
                self.n_list.append(v)
    
    def read_model(self, name):
        self.v_list = []
        self.n_list = []
        
        try:
            model = open(name, "rb")
        except:
            return 1

        vert_buf = [1, 1, 1]
        model.read(80)
        count = struct.unpack("I", model.read(4))[0]
        for i in range(count):
            model.read(12)
            for j in range(3):
                buf = model.read(12)
                vert_buf[j] = list(struct.unpack("3f", buf))[:]
            model.read(2)
            self.add_vertex(vert_buf)

        model.close()
        self.v_count = count * 3
        return 0
        
    def load_model(self, name):
        self.reset_view()
        self.read_model(name)
        self.size_hint = 1/self.size_hint
        self.size_hint = max(min(0.7, self.size_hint), 0.0001)
        self.initializeGL()

    def unload_model(self):
        self.can_show = False
        posAttrib = glGetAttribLocation(self.shaderProgram, b"position")
        glDisableVertexAttribArray(posAttrib)
        glDeleteBuffers(1, [self.vbo])
        glDeleteVertexArrays(1, [self.vao])
        
    def initializeGL(self):
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glShadeModel(GL_FLAT)
        glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)
        
        # get Vertex Array Object name
        self.vao = glGenVertexArrays(1)
        # set this new VAO to the active one
        glBindVertexArray(self.vao)
        # vertex data for one triangle
        triangle_vertices = self.v_list[:] + self.n_list[:]
        # convert to ctypes c_float array
        triangle_array = ((ctypes.c_float * len(triangle_vertices))
                          (*triangle_vertices))
        # get a VBO name from the graphics card
        self.vbo = glGenBuffers(1)
        # bind our vbo name to the GL_ARRAY_BUFFER target
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # move the vertex data to a new data store associated with our vbo
        glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(triangle_array),
                     triangle_array, GL_STATIC_DRAW)
        # vertex shader
        vertexShaderProgram = r"""#version 130
            in vec3 position;
            in vec3 normal;
            varying vec4 t_color;
            uniform float scale_z;
            void main() {
                mat4 scale_m = mat4(
                    1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, scale_z, 0.0,
                    0.0, 0.0, 0.0, 1.0);
                mat4 mvmatrix = scale_m * gl_ModelViewMatrix;
                gl_Position =  mvmatrix * vec4 (position, 1.0);
                const vec3 l = vec3(0.0, 0.0, 1.0);
                vec3 n = normalize(gl_NormalMatrix * normal);
                float snormal = dot(n, l);
                vec4 color;
                if (snormal < 0.0)
                    color = vec4 (-0.55, -0.55, -0.55, 1.0) * snormal;
                else
                    color = vec4 (0.25, 0.22, 0.0, 1.0) * snormal;
                    
                vec4 spec = vec4(0.6, 0.5, 0.0, 1.0) * pow(max(dot(n, normalize(vec3(0.0, 1.1, -1.0))), 0.0), 20.0);
                vec4 spec2 = vec4(0.5, 0.4, 0.0, 0.0) * pow(max(dot(n, normalize(vec3(0.0, -1.2, -1.0))), 0.0), 15.0);

                t_color = color + spec + spec2;
            }"""
        vertexShader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertexShader, vertexShaderProgram)
        glCompileShader(vertexShader)
        # fragment shader
        fragmentShaderProgram = r"""#version 130
            varying vec4 t_color;
            out vec4 outColor;
            void main() {
                outColor = t_color;
            }"""
        fragmentShader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragmentShader, fragmentShaderProgram)
        glCompileShader(fragmentShader)
        # shader program
        self.shaderProgram = glCreateProgram()
        glAttachShader(self.shaderProgram, vertexShader)
        glAttachShader(self.shaderProgram, fragmentShader)
        # color output buffer assignment
        glBindFragDataLocation(self.shaderProgram, 0, b"outColor")
        # link the program
        glLinkProgram(self.shaderProgram)
        # validate the program
        glValidateProgram(self.shaderProgram)
        # activate the program
        glUseProgram(self.shaderProgram)
        self.can_show = True
        self.setupViewport(self.width(), self.height())

    def mousePressEvent(self, event):
        self.lastPos = event.pos()
            
    def wheelEvent(self, event):
        self.zOff += self.zoom_scale * event.delta()
        if self.zOff <= 0:
            self.zOff = 0.00001
        self.updateGL()

    def reload_model(self, name):
        self.unload_model()
        self.load_model(name)
        self.updateGL()

    def reset_view(self):
        self.xOff =  0.0
        self.yOff = -0.5
        self.zOff =  0.9
        self.setXRotation(-90)
        self.setYRotation(0)
        self.setZRotation(180)
        self.updateGL()

    def mouseDoubleClickEvent(self, event):
        if event.buttons() & Qt.MiddleButton:
            self.reset_view()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.setXRotation(self.xRot - self.angle)
            self.updateGL()
        if event.key() == Qt.Key_Down:
            self.setXRotation(self.xRot + self.angle)
            self.updateGL()
        if event.key() == Qt.Key_Right:
            self.setZRotation(self.zRot + self.angle)
            self.updateGL()
        if event.key() == Qt.Key_Left:
            self.setZRotation(self.zRot - self.angle)
            self.updateGL()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.xOff += self.move_scale * dx
            self.yOff -= self.move_scale * dy
        elif event.buttons() & Qt.RightButton:
            self.setXRotation(self.xRot - self.angle_scale * dy)
            self.setZRotation(self.zRot - self.angle_scale * dx)
        elif event.buttons() & Qt.MiddleButton:
            self.zOff += self.size_scale * dy
            if self.zOff <= 0:
                self.zOff = 0.00001
            
        self.lastPos = event.pos()
        self.updateGL()

    def normalizeAngle(self, angle):
        if angle < 0:
            angle = 360 + angle % 360
        elif angle > 359:
            angle = angle % 360
        return angle

    def resizeGL(self, width, height):
        self.setupViewport(width, height)

    def setupViewport(self, width, height):
        side = max(width, height)
        glViewport((width - side) // 2, (height - side) // 2, side, side)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glDisable(GL_CLIP_PLANE0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        self.qglClearColor(self.clearColor)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Change scroll offset
        #glScalef(self.zOff, self.zOff, self.zOff)
        glTranslatef(self.xOff, self.yOff, 0.0)
        glScalef(self.zOff, self.zOff, self.zOff)
        glRotatef(self.xRot, 1.0, 0.0, 0.0)
        glRotatef(self.yRot, 0.0, 1.0, 0.0)
        glRotatef(self.zRot, 0.0, 0.0, 1.0)
        loc = glGetUniformLocation(self.shaderProgram, b"scale_z")
        glUniform1f(loc, self.size_hint/self.zOff);

        if self.can_show:
            # Choose buffer; triangles
            posAttrib = glGetAttribLocation(self.shaderProgram, b"position")
            glEnableVertexAttribArray(posAttrib)
            glVertexAttribPointer(posAttrib,
                                  3,
                                  GL_FLOAT,
                                  False,
                                  0,
                                  ctypes.c_voidp(0))
            
            nAttrib = glGetAttribLocation(self.shaderProgram, b"normal")
            glEnableVertexAttribArray(nAttrib)
            glVertexAttribPointer(nAttrib,
                                  3,
                                  GL_FLOAT,
                                  False,
                                  0,
                                  ctypes.c_voidp(
                                      self.v_count * 3 * sizeof(ctypes.c_float)))

            # Draw triangles
            glDrawArrays(GL_TRIANGLES, 0, self.v_count)

        # Floor
        glBegin(GL_LINES)
        for i in range(21):
            glVertex3f(-1.0 + 0.1 * i, -1.0, 0.0)
            glVertex3f(-1.0 + 0.1 * i, +1.0, 0.0)
            glVertex3f(-1.0, -1.0 + 0.1 * i, 0.0)
            glVertex3f(+1.0, -1.0 + 0.1 * i, 0.0)
        glEnd()

    def setXRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle

    def setYRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle

    def setZRotation(self, angle):
        angle = self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
# End of 3D widget

def create_blank_config():
    config = configparser.ConfigParser()
    config.add_section("Main")
    config.add_section("Tools")
    config.add_section("Export")
    config.set("Main", "last_base", "")
    config.set("Main", "language", detect_locale())
    if os.path.isdir(lpath+"tools\\Blender"):
        bpath = lpath+"tools\\Blender"
    elif os.path.isdir("C:\\Program Files (x86)\\Blender Foundation\\Blender"):
        bpath = "C:\\Program Files (x86)\\Blender Foundation\\Blender"
    else:
        bpath = "C:\\Program Files\\Blender Foundation\\Blender"
    config.set("Tools", "blender", bpath + "\\blender.exe")
    config.set("Tools", "unpacker",
               lpath+"tools\\BD_extract\\DXMDExtract.exe")
    config.set("Tools", "tex_converter",
               lpath+"tools\\texture_converter\\TXET2DDS.exe")
    config.set("Tools", "dds_converter",
               lpath+"tools\\texture_converter\\sctexconv_1.3.exe")
    config.set("Export", "directory", "")
    config.set("Export", "texture_format", "")
    config.set("Export", "model_format", "")

    with open("config.txt", "w") as config_file:
        config.write(config_file)

def read_config():
    global path
    global dds_converter
    global tex_converter
    global unpacker
    global blender
    global epath
    global ext_textures
    global ext_models
    global lang_name
    global last_dir

    config = configparser.ConfigParser()
    config.read(lpath+"config.txt")
    path = config.get("Main", "last_base")
    lang_name = detect_locale(config.get("Main", "language"))
    blender = config.get("Tools", "blender")
    unpacker = config.get("Tools", "unpacker")
    tex_converter = config.get("Tools", "tex_converter")
    dds_converter = config.get("Tools", "dds_converter")
    epath = config.get("Export", "directory")
    if len(epath) > 0 and epath[-1] != "\\":
        epath += "\\"
    if last_dir == "" and len(epath) > 0: last_dir = epath[:-1]
    ext_textures = config.get("Export", "texture_format")
    ext_models = config.get("Export", "model_format")

def write_config():
    config = configparser.ConfigParser()
    config.add_section("Main")
    config.add_section("Tools")
    config.add_section("Export")
    config.set("Main", "last_base", path)
    config.set("Main", "language", lang_name)
    config.set("Tools", "blender", blender)
    config.set("Tools", "unpacker", unpacker)
    config.set("Tools", "tex_converter", tex_converter)
    config.set("Tools", "dds_converter", dds_converter)
    config.set("Export", "directory", epath)
    config.set("Export", "texture_format", ext_textures)
    config.set("Export", "model_format", ext_models)

    with open("config.txt", "w") as config_file:
        config.write(config_file)

# Locale set
def detect_locale(lang_name=None):
    if lang_name == None:
        if os.name == "nt":
            lang_name = locale.windows_locale[ctypes.windll.kernel32.\
                                           GetUserDefaultUILanguage()]
        else:
            lang_name = locale.getdefaultlocale()[0]

    if lang_name not in langs:
        lang_name = langs[0]
    return lang_name

def create_blender_script():
    with open(lpath + "tools/blender_script.py", "w") as blender_script:
        blender_script.write(r"""import os
import bpy
import sys

# Names of folder and files
args = sys.argv

source_file = args[-2]
convert_file = args[-1]
save_type = convert_file.split(".")[-1]

# Deleting all objects
for scene in bpy.data.scenes:
    for obj in scene.objects:
        scene.objects.unlink(obj)
for bpy_data_iter in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.lamps,
        bpy.data.cameras,
        ):
    for id_data in bpy_data_iter:
        bpy_data_iter.remove(id_data)
bpy.ops.object.select_by_type(type = "MESH")
bpy.ops.object.delete(use_global=False)
for item in bpy.data.meshes:   
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            scene.objects.unlink(obj) 
    item.user_clear()
    bpy.data.meshes.remove(item)
print("Scene cleared")

# Open model and save
try:
    try:
        print("Try to use plugin...")
        bpy.ops.import_scene.deusexmd(filepath=source_file)
        print("Success")
    except:
        try:
            print("Fail")
            print("Try to use outer script...")
            try:
                import import_DeusExMD
            except:
                print("Fail to import")
                exit(2)
            print("Successful module import; try to open model...")
            import_DeusExMD.import_DeusExMD(source_file, #filepath
                                        bpy.context, #context
                                        False, #randomize_colors
                                        True, #import_vertcolors
                                        False, #skip_blank
                                        False, #use_layers
                                        1.0) #mesh_scale
            print("Success")
        except:
            print("Fail")
            exit(1)

    print("\nModel opened\n")
    if save_type == "obj":
        bpy.ops.export_scene.obj(filepath=convert_file)
    elif save_type == "fbx":
        bpy.ops.export_scene.fbx(filepath=convert_file)
    elif save_type == "3ds":
        bpy.ops.export_scene.autodesk_3ds(filepath=convert_file)
    elif save_type == "stl":
        bpy.ops.export_mesh.stl(filepath=convert_file,
                                 check_existing=False,
                                 ascii=False)
    else:
        print("Incorrect save format")
    print("\nConvertions done!")
    exit(0)

# In case of error
except Exception:
    print("\nSome errors here")
    exit(1)
""")

def init_folders():
    is_first_launch = 0
    
    if not os.path.isfile(lpath+"config.txt"):
        create_blank_config()
        is_first_launch += 3
    if not os.path.isdir(tpath):
        os.mkdir(tpath)
        is_first_launch += 1
    if not os.path.isdir(lpath + "tools"):
        os.mkdir(lpath + "tools")
        is_first_launch += 2
    if not os.path.isdir(lpath + "tools/BD_extract"):
        os.mkdir(lpath + "tools/BD_extract")
        is_first_launch += 1
    if not os.path.isdir(lpath + "tools/texture_converter"):
        os.mkdir(lpath + "tools/texture_converter")
        is_first_launch += 1
    if not os.path.isdir(lpath + "tools/texture_converter"):
        os.mkdir(lpath + "tools/Models")
        is_first_launch += 1
    if not os.path.isfile(lpath + "tools/blender_script.py"):
        is_first_launch += 1
        create_blender_script()
    read_config()

    if not os.path.isfile(blender) or not os.path.isfile(unpacker) or\
       not os.path.isfile(tex_converter) or not os.path.isfile(dds_converter):
        is_first_launch += 3
    else:
        is_first_launch -= 1

    if is_first_launch > 3:
        global first_launch
        first_launch = True

def shift(arr):
    offset = 0
    for element in arr:
        if type(element) == int:
            offset += element
    return offset

# Load folders
def load_folders(path):
    global folder_tree
    if path == "" or not os.path.isdir(path) or\
    not os.path.isfile(path+"NameMap.txt"):
        return
    else:
        folder_tree = {}
    for line in os.listdir(path):
        if os.path.isdir(path+line):
            for file in os.listdir(path+line):
                folder_tree.update({file: line})

# Load base
def load_base(base_file):
    global tree_list
    base = open(base_file, "r")
    for line in base.readlines():
        if len(line) > 3:
            tree_list.append([])
            buf = line.split(";")[:-1]
            for el in buf:
                la = el.split(":")
                l1 = int(la[1])
                if l1 != -1:
                    l2 = int(la[2])
                else:
                    l2 = la[2]
                tree_list[-1].append([la[0], l1, l2])
    base.close()

# Return branch with leaves; x, y - branch node
def add_leaf(x, y):
    if tree_list[y][x][1] == -1: # Add file
        leaf = QTreeWidgetItem(None, [tree_list[y][x][0], tree_list[y][x][2]])
        leaf.setIcon(0, QIcon(icons.get(tree_list[y][x][0].split(".")[-1], None)))
        return leaf
    else:
        arr = [] # Add list of children
        for i in range(tree_list[y][x][1],
                       tree_list[y][x][1] + tree_list[y][x][2]):
            arr.append(add_leaf(i, y + 1))
        branch = QTreeWidgetItem(None, [tree_list[y][x][0],
                                        str(tree_list[y][x][2])])
        branch.addChildren(arr)
        return branch

# Build a tree widget ierarchy
def build_tree():
    global tree_list
    global cur_item
    cur_item = QTreeWidgetItem()
    tree.clear()
    widget.statusBar().showMessage(app.translate("BuildTree",
                                                 "Build a file tree"))
    load_base(path+"converted_base.txt")
    if len(tree_list) == 0:
        error_window = QMessageBox.critical(None, "Empty base",
                                            "Converted base is empty")
        return
    for i in range(len(tree_list[0])):
        tree.addTopLevelItem(add_leaf(i, 0))
    tree.sortItems(0, Qt.AscendingOrder)
    tree_list = []

def convert_base():
    base = open(path+"NameMap.txt", "r")

    tree_list = []

    lc = len(base.readlines())
    base.seek(0)
    pj = 1

    convertWindow = QWidget()
    convertWindow.setWindowTitle(app.translate("ConvertTitle", "Convert names"))
    convertWindow.resize(350, 100)
    convertWindow.setWindowFlags(Qt.ToolTip)
    
    convertLayout = QVBoxLayout(convertWindow)
    
    convertProgress = QProgressBar(parent = convertWindow)
    convertProgress.setMaximum(lc)

    convertLabel = QLabel(app.translate("ConvertText", "Please wait:  file tree's creation is going (only at the first launch)"),
                          parent = convertWindow)
    convertLabel.setWordWrap(True)
    convertLabel.setAlignment(Qt.AlignCenter)

    convertLayout.addWidget(convertLabel)
    convertLayout.addWidget(convertProgress)

    convertWindow.show()

    for line in base.readlines():
        convertProgress.setValue(pj)
        pj += 1
        ext = line.split(".")[-1][:-1]
        #or ext not in ext_types
        if ext not in ext_types or\
           line.count("[", 38) != 1 or line[39:48] != "assembly:":
            continue
        leaf = line[21:37] # File hash (name)
        if leaf+".bin" not in folder_tree:
            #print("Not a real file", line)
            continue
        line = line[48:line.rindex("]")]
        line = line.replace("?", "") # del ? sign
        #line += "?" + ext
        buf = line.split("/")[1:] # Folders
        buf[-1], leaf = leaf, buf[-1]
        length = len(buf)

        # Scale up base
        if length*2 > len(tree_list):
            for i in range(length*2 - len(tree_list)):
                tree_list.append([])

        index = 0
        for i in range(length):
            if i == 0: # Top level folders
                if buf[0] not in tree_list[0]: # Add new
                    index = len(tree_list[0]) # Remember it's index
                    tree_list[0].append(buf[0]) # Add it's name
                    tree_list[1].append(0) # Add count of it's children
                else:
                    index = tree_list[0].index(buf[0]) # Remember it's index
            else:
                lb = shift(tree_list[i*2 - 1][:index]) # Number of elements before
                if type(tree_list[i*2 - 1][index]) == str:
                    #print("BAD LEAF!", buf[i], tree_list[i*2][index])
                    break
                rb = lb + tree_list[i*2 - 1][index] # add elements of this folder
                
                if buf[i] in tree_list[i*2][lb:rb]: # If we have this element
                    index = tree_list[i*2].index(buf[i], lb, rb) # Remember it's index
                else:
                    tree_list[i*2-1][index] += 1 # Increase parent counter
                    index = lb # Index of new element
                    if i == length - 1: # If file
                        tree_list[i*2 + 1].insert(index, leaf) # Store it's hash
                    else:
                        tree_list[i*2 + 1].insert(index, 0) # Init parent counter
                    tree_list[i*2].insert(index, buf[i]) # Store name

    base.close()

    base = open(path+"converted_base.txt", "w")

    for i in range(len(tree_list)//2):
        offset = 0
        for j in range(len(tree_list[i*2])):
            if type(tree_list[i*2+1][j]) == str:
                base.write("{:}:{:}:{:};".format(tree_list[i*2+1][j],
                                                 -1, tree_list[i*2][j]))
            else:
                base.write("{:}:{:}:{:};".format(tree_list[i*2][j], offset,
                           tree_list[i*2+1][j]))
                offset = offset + tree_list[i*2+1][j]
        base.write("\n")

    base.close()
    convertWindow.close()

def open_base():
    global path
    if not os.path.isfile(path+"NameMap.txt"):
        fileName = QFileDialog.getOpenFileName(
            caption=app.translate("OpenBase", "Open converted base"),
            dir = "", filter="DEMD namemap (NameMap.txt)")
        if fileName[0] == "":
            return
        path = os.path.dirname(fileName[0])+"/"

    load_folders(path)
    if not os.path.isfile(path+"converted_base.txt"):
        widget.statusBar().showMessage(app.translate("BaseConvert",
                                                     "Convert base"))
        convert_base()
    write_config()
    build_tree()
    widget.statusBar().showMessage(app.translate("Ready", "Ready"))

def convert_DEMD_base():
    global path
    demd_dir = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Deus Ex \
Mankind Divided\\runtime"
    if not os.path.isdir(demd_dir):
        demd_dir = "C:\\Program Files\\Steam\\steamapps\\common\\Deus Ex \
Mankind Divided\\runtime"
    if not os.path.isdir(demd_dir):
        demd_dir = "C:\\"
    game_folder = QFileDialog.getExistingDirectory(
        caption=app.translate("OpenGameFolder", "Open DEMD runtime folder"),
        dir = demd_dir)
    if game_folder == "":
        return
    
    path = QFileDialog.getExistingDirectory(
        caption=app.translate("OpenBaseSaveFolder",
                        "Where to unpack base (need about 23gb of free space)"))

    if path == "":
        return
    res = subprocess.call([unpacker, game_folder, path], shell=False)
    if res != 0 or not os.path.isfile(path+"NameMap.txt"):
        error_mess = QMessageBox.critical(
            None, app.translate("ConvertError", "Convertion error"),
            app.translate("ConvertErrorText",
                          "Looks like base convertion failed.\nCheck your actions and/or read help."))

def change_lang():
    global app
    global translation
    translation = QTranslator()
    if os.path.isfile("lang_"+lang_name) or\
       os.path.isfile("lang_"+lang_name.split("_")[0]):
        translation.load("lang_"+lang_name)
    else:
        translation.load(":lang_"+lang_name)

    app.installTranslator(translation)


# Open settings
init_folders()

# Enable translation
#translation = QTranslator()
#translation.load("lang_"+lang_name)

app = QApplication(sys.argv)
#app.installTranslator(translation)
change_lang()

# App icon
app.setWindowIcon(QIcon(":/ico.png"))

# Main widget
widget = QMainWindow()
widget.setMinimumSize(350, 350)
widget.resize(640, 350)
widget.setWindowTitle(app.translate("AppTitle", "DEMD database"))

widget.statusBar().showMessage(app.translate("Ready", "Ready"))

# Central widget
centre = QSplitter(Qt.Horizontal)
widget.setCentralWidget(centre)

# Tree widget
tree = QTreeWidget(parent=centre)
tree.setColumnCount(2)
tree.setFrameStyle(QFrame.Box | QFrame.Sunken)
tree.header().setStretchLastSection(False)
tree.header().setResizeMode(0, QHeaderView.Stretch)
tree.header().close()
tree.setColumnHidden(1, True)

# Viewport widget
viewport = QLabel(parent=centre)
viewport.setFrameStyle(QFrame.Panel | QFrame.Sunken)
viewport.setMinimumSize(300, 300)

vp3D = GLWidget(parent=viewport)

vpTopLayout = QVBoxLayout(viewport)

vpLayout = QStackedLayout(viewport)

class ImageView(QLabel):
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent,)
        # Model screen position and scale
        self.xOff = 0.0
        self.yOff = 0.0
        self.scaleImage = 1.0
        self.move_scale = 1.0
        self.zoom_scale = 0.001
        self.size_scale = 0.002
        # Last mouse pos
        self.lastPos = QPoint()
      
    def wheelEvent(self, event):
        self.scaleImage += self.zoom_scale * event.delta()
        if self.scaleImage < 0:
            self.scaleImage = 0.0
        self.resize_image()

    def reset_view(self):
        self.xOff = 0.0
        self.yOff = 0.0
        self.scaleImage = 1.0
        self.resize_image()

    def mouseDoubleClickEvent(self, event):
        if event.buttons() & Qt.MiddleButton:
            self.reset_view()

    def mouseMove(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            self.xOff += self.move_scale * dx
            self.yOff += self.move_scale * dy
        elif event.buttons() & Qt.MiddleButton:
            self.scaleImage += self.size_scale * dy
            if self.scaleImage < 0:
                self.scaleImage = 0.0

        self.resize_image()
        self.lastPos = event.pos()
    
    def resize_image(self):
        new_pix = vpPixmap.scaled(viewport.size()*self.scaleImage,
                                      aspectMode=Qt.KeepAspectRatio)
        self.resize(new_pix.size())
        c = viewport.rect().center()
        self.setPixmap(new_pix)
        self.move(c.x() - self.width() / 2 + self.xOff,
                  c.y() - self.height() / 2 + self.yOff)


class ImageParent(QLabel):
    def resizeEvent(self, size):
        vpImage.reset_view()

    def mouseDoubleClickEvent(self, event):
        vpImage.mouseDoubleClickEvent(event)
            
    def wheelEvent(self, event):
        vpImage.wheelEvent(event)

    def mouseMoveEvent(self, event):
        vpImage.mouseMove(event)

    def mousePressEvent(self, event):
        vpImage.lastPos = event.pos()

vpIBase = ImageParent(parent=viewport)
vpImage = ImageView(parent=vpIBase)
vpImage.setPixmap(QPixmap(1,1))
vpPixmap = QPixmap()

vpFilename = QLabel("\n", parent=viewport)
vpFilename.setAlignment(Qt.AlignTop)
vpFilename.setFont(QFont("", 7))
vpFilename.setAutoFillBackground(True)
vpFilename.setStyleSheet("background-color: white")

vpTopLayout.setSpacing(0)
vpTopLayout.setContentsMargins(0, 0, 0, 0)
vpTopLayout.addWidget(vpFilename, 0)
vpLayout.addWidget(vp3D)
vpLayout.addWidget(vpIBase)
vpTopLayout.addLayout(vpLayout, 1)

def convert_model(source, destination):
    int_ext = file_name.split(".")[-1]
    ext = destination.split(".")[-1]
    if os.path.isfile(source):
        if ext == "bin":
            shutil.copyfile(source, destination)
            if int_ext != "apx":
                return 0
    else:
        return -1
    if int_ext == "apx":
        if ext != "stl":
            destination = destination[:-3] + "obj"
        if ext == "bin":
            destination = destination[:-3] + "apb"
        res = subprocess.call([lpath+"tools\\Models\\XEPA2model.exe",
                               source, destination],
                                shell=False)
    else:
        log = open("blender_convert.log", "w")
        res = subprocess.call([blender, "-b", "-Y", "--addons",
                               "io_scene_DeusEx-MD", "-P",
                               lpath+"\\tools\\blender_script.py", "--",
                                source, destination],
                                shell=False, stdout=log)
        log.close()

    return res

def convert_image(source, destination):
    ext = destination.split(".")[-1]
    if os.path.isfile(source):
        if ext == "tex":
            shutil.copyfile(source, destination)
            return 0
    else:
        return -1
    
    res = subprocess.call([tex_converter, source,
                           tpath+"texture.dds"],
                           shell=False)
    if res == 0 and ext == "dds":
        shutil.copyfile(tpath+"texture.dds", destination)
        return 0
    if res == 0 and ext != "dds":
        if os.path.isfile(tpath+"texture."+ext):
            os.remove(tpath+"texture."+ext)

        #tif / png / tga / jpg
        conf_name = os.path.dirname(tex_converter) + "/config.txt"
        def set_tex_conf(path, ext):
            conf = open(path, "w")
            conf.write(r"""verbose = false
recursive = false
clean = true
merge_gloss = true
format = """)
            conf.write(ext)
            conf.close()
            
        if os.path.isfile(conf_name):
            conf_file = open(conf_name, "r")
            conf = conf_file.readlines()
            conf_file.close()
            for line in conf:
                if line[:6] == "format" and line != "format = "+ext+"\n":
                    set_tex_conf(conf_name, ext)
                    break
        else:
            set_tex_conf(conf_name, ext)

        for file in os.listdir(os.path.dirname(tex_converter)):
            if file[:23] == "sctextureconverter_log_" and file[-4:] == ".txt":
                os.remove(os.path.dirname(tex_converter)+"\\"+file)

        res = subprocess.call([dds_converter, tpath],
                               shell=False, stdout=subprocess.DEVNULL)
        if res == 0:
            if destination != (tpath+"texture."+ext):
                shutil.copyfile(tpath+"texture."+ext, destination)
        return res
    else:
        return 1


def convert_audio(source, destination):
    if not os.path.isfile(source):
        return -1
    try:
        with open(source, "rb") as f:
            data = f.read()
            is_resource = False
            index = 0
            while data:
                fsb = fsb5.load(data)
                ext = fsb.get_sample_extension()
                data = data[fsb.raw_size:]
                if not is_resource and data:
                    is_resource = True

                for sample in fsb.samples:
                    try:
                        sample_data = fsb.rebuild_sample(sample)
                    except ValueError as e:
                        return -2
                    with open(destination+"."+ext, "wb") as f:
                        written = f.write(sample_data)
                        
                index += 1
    except:
        return -2
    return 0

def update_viewport(cur_file, file_title):
    global vpPixmap
    ext = file_title.split(".")[-1]
    if ext in types_3d:
        widget.statusBar().showMessage(app.translate("3DModel", "3d model"))
        res = convert_model(path+cur_file, tpath+"model.stl")
        if res == 0:
            vp3D.reload_model(tpath+"model.stl")
            #widget.statusBar().showMessage("Done!")
            vpLayout.setCurrentIndex(0)
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))
        
    if ext in types_tex:
        widget.statusBar().showMessage(app.translate("Texture", "Texture"))
        viewport.setPixmap(QPixmap())
        res = convert_image(path+cur_file, tpath+"texture.png")
        if res == 0:
            vpPixmap = QPixmap(tpath+"texture.png")
            vpImage.reset_view()
            #widget.statusBar().showMessage("Done!")
            vpLayout.setCurrentIndex(1)
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))

    if ext in types_audio:
        widget.statusBar().showMessage(app.translate("Audio", "Audio"))

def change_item(item):
    global cur_file
    global file_name
    global file_parent
    global cur_hash
    global cur_item
    #if item == None or item == cur_item:
    #    return
    cur_item = item
    if item.childCount() == 1:
        item = item.child(0)
    #if item == cur_item:
    #    return
    if item.childCount() == 0 and len(item.text(1)) == 16:
        cur_hash = item.text(1)
        cur_file = folder_tree.get(cur_hash+".bin", "")+\
                         "/"+cur_hash+".bin"
        file_name = item.text(0)
        file_parent = item.parent().text(0)
        vpFilename.setText(cur_file+"\n"+file_parent+" : "+file_name)
        update_viewport(cur_file, file_name)

tree.currentItemChanged.connect(change_item)

# Central layout
centre.setCollapsible(0, False)
centre.setCollapsible(1, False)

# Create file menu
file_menu = widget.menuBar().addMenu(app.translate("FileMenu", "File"))

# Add unpacking DEMD base
convertDEMDAction = QAction(app.translate("DEMDConvert", "Unpack game DB"),
                            widget)
convertDEMDAction.setStatusTip(app.translate("DEMDTip", "Unpack game archieves"))
widget.connect(convertDEMDAction, SIGNAL("triggered()"), convert_DEMD_base)
file_menu.addAction(convertDEMDAction)

# Add base opening
openAction = QAction(app.translate("BaseOpen", "Open unpacked DB"), widget)
openAction.setStatusTip(app.translate("OpenTip", "Open game files in program"))
openAction.setShortcut("Ctrl+O")
widget.connect(openAction, SIGNAL("triggered()"), open_base)
file_menu.addAction(openAction)

file_menu.addSeparator()

def file_export():
    global file_name
    global file_parent
    global cur_hash
    global last_dir
    global last_filter
    if file_name == "" or cur_hash == "":
        return

    ext = file_name.split(".")[-1]
    if ext in types_3d:

        if file_name == "ground.weightedprim":
            name = file_parent.split(".")[0]
        else:
            name = file_name.split(".")[0]

        save_name = QFileDialog.getSaveFileName(
            caption=app.translate("Export3d", "Export model"),
            dir = last_dir+"\\"+name, filter = save_filter[0],
            selectedFilter = last_filter[0])
        if save_name[0] == "":
            return
        last_dir = os.path.dirname(save_name[0])
        last_filter[0] = save_name[1]
        
        res = convert_model(path+cur_file,
                            save_name[0])
                            
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))
        
    elif ext in types_tex:
        if file_name == "default.tex":
            name = file_parent.split(".")[0]
        else:
            name = file_name.split(".")[0]

        save_name = QFileDialog.getSaveFileName(
            caption=app.translate("ExportTex", "Export texture"),
            dir = last_dir+"\\"+name, filter = save_filter[1],
            selectedFilter = last_filter[1])
        if save_name[0] == "":
            return
        last_dir = os.path.dirname(save_name[0])
        last_filter[1] = save_name[1]
            
        res = convert_image(path+cur_file, # cur_hash file_name
                            save_name[0])
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))

    elif ext in types_audio:
        name = file_name

        save_name = QFileDialog.getSaveFileName(
            caption=app.translate("ExportAudio", "Export audio"),
            dir = last_dir+"\\"+name)
        if save_name[0] == "":
            return
        last_dir = os.path.dirname(save_name[0])
        
        res = convert_audio(path+cur_file, save_name[0])
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))

    else:
        try:
            if not os.path.isfile(path+cur_file):
                widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
                return            
            name = file_name
            save_name = QFileDialog.getSaveFileName(
                caption=app.translate("ExportFile", "Export file"),
                dir = last_dir+"\\"+name)
            if save_name[0] == "":
                return
            last_dir = os.path.dirname(save_name[0])
            
            shutil.copyfile(path+cur_file, save_name[0])
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        except:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))

# Add export
exportAction = QAction(app.translate("MenuExport", "Export as..."), widget)
exportAction.setStatusTip(app.translate("ExportTip",
                                        "Save file in common formats"))
exportAction.setShortcut("Ctrl+S")
widget.connect(exportAction, SIGNAL("triggered()"), file_export)
file_menu.addAction(exportAction)


def short_path(path, line_len=45):
    if len(path) > line_len:
        arr = path.split("\\")
        if len(arr) > 3:
            new_len = len(arr[0]) + len(arr[-1]) + 2
            if new_len < line_len - 3:
                new_arr = [arr[0], arr[-1]]
                ind = 1
                for i in range(len(arr)-2):
                    if i%2 != 0:
                        element = arr[i//2+1]
                    else:
                        element = arr[-2-i//2]
                    new_len += len(element) + 1
                    if new_len < line_len - 3:
                        new_arr.insert(ind, element)
                        if i&1: ind += 1
                    else:
                        break
                new_arr.insert(ind, "...")
                return "\\".join(new_arr)
        return "...\\"+arr[-1]
    return path

class PathButton(QPushButton):
    def __init__(self, dialog_title="", is_folder=False, filter=""):
        super(PathButton, self).__init__()
        self.path = ""
        self.is_folder = is_folder
        self.dialog_title = dialog_title
        self.clicked.connect(self.changePath)
        self.filter = filter

    def updatePath(self, path):
        path = path.replace("/", "\\")
        if self.is_folder and len(path) > 0 and path[-1] != "\\":
            path += "\\"
        if self.is_folder and os.path.isdir(path) or\
           not self.is_folder and os.path.isfile(path):
            self.setStyleSheet("background: rgb(150, 255, 150)")
        else:
            self.setStyleSheet("background: rgb(255, 150, 150)")
        self.setToolTip(path)
        self.setText(short_path(path))
        self.path = path

    def changePath(self):
        if self.is_folder:
            new_path = QFileDialog.getExistingDirectory(
                caption=self.dialog_title, dir=self.path)
        else:
            new_path = QFileDialog.getOpenFileName(
                caption=self.dialog_title,
                dir=os.path.dirname(self.path),
                filter=self.filter)[0]
        if new_path == "":
            return
        else:
            self.updatePath(new_path)
        

# Settings
settingsWindow = QWidget()
settingsWindow.resize(350,290)
settingsWindow.setWindowTitle(app.translate("SettingsTitle", "Settings"))

settingsTab1 = QWidget()
settingsTab1Layout = QFormLayout(parent=settingsTab1)

settingsLang = QComboBox(parent=settingsTab1)
settingsLang.addItems(langs)
settingsTab1Layout.addRow(app.translate("SettingsLang", "App language"),
                          settingsLang)
settingsBlender = PathButton(
    dialog_title=app.translate("BlenderDialog", "Choose blender.exe"),
    filter="Blender 3D (blender.exe)")
settingsTab1Layout.addRow(app.translate("SettingsBlender", "Blender path"),
                          settingsBlender)
settingsUnpack = PathButton(app.translate("UnpackerDialog",
                                          "Choose Sir Kane's DEMDExtractor"))
settingsTab1Layout.addRow(app.translate("SettingsUnpack", "Archive unpacker"),
                          settingsUnpack)
settingsTex = PathButton(app.translate("TEX2DDSDialog",
                                       "Choose Tex2Dds converter"))
settingsTab1Layout.addRow(app.translate("SettingsTex", "Tex2DDS converter"),
                          settingsTex)
settingsDds = PathButton(app.translate("DDSDialog",
                                       "Choose dds to image converter"))
settingsTab1Layout.addRow(app.translate("SettingsDDS", "DDS image converter"),
                          settingsDds)

settingsTab2 = QWidget()
settingsTab2Layout = QFormLayout(parent=settingsTab2)

settingsPath = PathButton(app.translate("EPathDialog",
                                        "Choose folder for fast export"),
                          True)
settingsTab2Layout.addRow(app.translate("SettingsPath", "Fast export savepath"),
                          settingsPath)
settingsImage = QComboBox(parent=settingsTab2)
settingsImage.addItems(save_ext_tex)
settingsTab2Layout.addRow(app.translate("SettingsImage", "Image format"),
                          settingsImage)
settingsModel = QComboBox(parent=settingsTab2)
settingsModel.addItems(save_ext_3d)
settingsTab2Layout.addRow(app.translate("SettingsModel", "Models format"),
                          settingsModel)

settingsTab = QTabWidget(parent=settingsWindow)

settingsTab.addTab(settingsTab1,
                   app.translate("SettingsTabCommon", "Common"))
settingsTab.addTab(settingsTab2,
                   app.translate("SettingsTabExport", "Fast export"))

def update_settings():
    global path
    global dds_converter
    global tex_converter
    global unpacker
    global blender
    global epath
    global ext_textures
    global ext_models
    global lang_name
    global last_dir

    blender = settingsBlender.path
    unpacker= settingsUnpack.path
    tex_converter = settingsTex.path
    dds_converter = settingsDds.path
    epath = settingsPath.path

    if lang_name != settingsLang.currentText():
        lang_name = settingsLang.currentText()
        warn = QMessageBox.information(
            None, app.translate("LangChangeTip", "Language change"),
            app.translate("LangChangeText",
                          "Restart app to enable selected language"))
    ext_textures = settingsImage.currentText()
    ext_models = settingsModel.currentText()
    
    write_config()
    settingsWindow.close()

def prepare_settings():
    if lang_name in langs:
        settingsLang.setCurrentIndex(langs.index(lang_name))
    else:
        settingsLang.setCurrentIndex(0)
    
    settingsBlender.updatePath(blender)
    settingsUnpack.updatePath(unpacker)
    settingsTex.updatePath(tex_converter)
    settingsDds.updatePath(dds_converter)

    settingsPath.updatePath(epath)
    
    if ext_textures in save_ext_tex:
        settingsImage.setCurrentIndex(save_ext_tex.index(ext_textures))
    else:
        settingsImage.setCurrentIndex(0)
    if ext_models in save_ext_3d:
        settingsModel.setCurrentIndex(save_ext_3d.index(ext_models))
    else:
        settingsModel.setCurrentIndex(0)

settingsButtonLayout = QHBoxLayout()
settingsApply = QPushButton(app.translate("Save", "Save"),
                            parent=settingsWindow)
settingsApply.clicked.connect(update_settings)
settingsCancel = QPushButton(app.translate("Cancel", "Cancel"),
                             parent=settingsWindow)
settingsCancel.clicked.connect(settingsWindow.close)

settingsButtonLayout.addWidget(settingsApply)
settingsButtonLayout.addWidget(settingsCancel)
settingsLayout = QVBoxLayout(settingsWindow)
settingsLayout.addWidget(settingsTab, 1)
settingsLayout.addLayout(settingsButtonLayout)

def showSettings(tab=0):
    prepare_settings()
    settingsTab.setCurrentIndex(tab)
    settingsWindow.show()

def configure_fast_export():
    info = QMessageBox.information(
        None, app.translate("FastExportSettingsTip",
                            "Need configure fast export"),
        app.translate("FastExportSettingsText",
                      "Before using fast export, you need configure output folder and formats first"))
    showSettings(1)

def fast_export():
    global file_name
    global file_parent
    global cur_hash
    global cur_file
    if file_name == "" or cur_hash == "":
        return

    if ext_models == "" or ext_textures == "" or epath == "":
        configure_fast_export()
        return

    if not os.path.isdir(epath):
        try:
            os.mkdir(epath)
        except:
            configure_fast_export()
            return
    if not os.path.isdir(epath):
        configure_fast_export()
        return

    j = 1
    ext = file_name.split(".")[-1]
    if ext in types_3d:
        if file_name == "ground.weightedprim":
            name = file_parent.split(".")[0]
        else:
            name = file_name.split(".")[0]
        sname = name + "." + ext_models
        while os.path.isfile(epath+sname):
            sname = name + "_" + str(j) + "." + ext_models
            j += 1
        res = convert_model(path+cur_file, epath+sname)
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))           
        
    elif ext in types_tex:
        if file_name == "default.tex":
            name = file_parent.split(".")[0]
        else:
            name = file_name.split(".")[0]
        sname = name + "." + ext_textures
        while os.path.isfile(epath+sname):
            sname = name + "_" + str(j) + "." + ext_textures
            j += 1
        res = convert_image(path+cur_file, epath+sname)
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))

    elif ext in types_audio:
        name = file_name.split(".")[0]
        sname = name
        while os.path.isfile(epath+sname+".ogg"):
            sname = name + "_" + str(j)
            j += 1
        res = convert_audio(path+cur_file, epath+sname)
        if res == 0:
            widget.statusBar().showMessage(app.translate("Ready", "Ready"))
        elif res == -1:
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
        else:
            widget.statusBar().showMessage(app.translate("CantConvert",
                                                         "Can't convert"))
            try:
                shutil.copyfile(path+cur_file, epath+file_name+"."+ext)
            except:
                pass

    else:
        if not os.path.isfile(path+cur_file):
            widget.statusBar().showMessage(app.translate("FileNotFound",
                                                         "File not found"))
            return
        name = file_name.split(".")[0]
        sname = name + "." + ext
        while os.path.isfile(epath+sname):
            sname = name + "_" + str(j) + "." + ext
            j += 1
        shutil.copyfile(path+cur_file, epath+sname)
        widget.statusBar().showMessage(app.translate("Ready", "Ready"))

# Add fast export
fastExportAction = QAction(app.translate("MenuFastExport", "Fast export"),
                           widget)
fastExportAction.setStatusTip(app.translate("FastExportTip",
                                            "Export file with chosen settings"))
fastExportAction.setShortcut("Ctrl+E")
widget.connect(fastExportAction, SIGNAL("triggered()"), fast_export)
file_menu.addAction(fastExportAction)

def mass_fast_export(par_item):
    global file_name
    global file_parent
    global cur_hash
    global cur_file
    
    if par_item.childCount() == 0 and len(par_item.text(1)) == 16:
        cur_hash = par_item.text(1)
        cur_file = folder_tree.get(cur_hash+".bin", "")+\
                         "/"+cur_hash+".bin"
        file_name = par_item.text(0)
        file_parent = par_item.parent().text(0)
        fast_export()
        return
    for i in range(par_item.childCount()):
        mass_fast_export(par_item.child(i))

def start_mass_export():
    if cur_item.text(0) == "" or cur_item.childCount() == 0 and\
       len(cur_item.text(1)) != 16:
        return
    if ext_models == "" or ext_textures == "" or epath == "":
        configure_fast_export()
        return
    mass_fast_export(cur_item)
    done = QMessageBox.information(
        None, app.translate("MassExportEnd", "Mass export complete"),
        app.translate("MassExportEndText",
                      "Export completed! New files in ")+epath)

# Add mass export
massExportAction = QAction(app.translate("MenuMassExport", "Mass fast export"),
                           widget)
massExportAction.setStatusTip(app.translate("MassExportTip",
                                            "Fast export for all childrens"))
widget.connect(massExportAction, SIGNAL("triggered()"), start_mass_export)
file_menu.addAction(massExportAction)

file_menu.addSeparator()

# Add preferences to menu
settingsAction = QAction(app.translate("MenuSettings", "Settings"), widget)
settingsAction.setStatusTip(app.translate("SettingsTip", "Set preferences"))
widget.connect(settingsAction, SIGNAL("triggered()"), showSettings)
file_menu.addAction(settingsAction)

file_menu.addSeparator()

# Add exit to menu
quitAction = QAction(app.translate("MenuExit", "Exit"), widget)
quitAction.setShortcut("Ctrl+Q")
quitAction.setStatusTip(app.translate("ExitTip", "Exit application"))
widget.connect(quitAction, SIGNAL("triggered()"), SLOT("close()"))
file_menu.addAction(quitAction)

# Create file menu
help_menu = widget.menuBar().addMenu(app.translate("HelpMenu", "Help"))

# Create HELP window
helpWindow = QWidget()
helpWindow.setMinimumSize(320, 240)
helpWindow.resize(500, 600)
helpWindow.setWindowTitle(app.translate("MenuHelp", "Help"))

helpContent = QTextBrowser()

helpLayout = QVBoxLayout(helpWindow)
helpLayout.setContentsMargins(0, 0, 0, 0)
helpLayout.addWidget(helpContent)

def showHelp():
    path = "help_"+lang_name+".html"
    if not os.path.isfile(path):
        path = "help_"+lang_name.split("_")[0]+".html"
        if not os.path.isfile(path):
            path = "help_en.html"
            if not os.path.isfile(path):
                widget.statusBar().showMessage(app.translate("CantOpenHelp",
                                                             "Can't open help"))
                return

    helpContent.setSource(QUrl(path))
    helpContent.clearHistory()
    helpWindow.show()

# Add help
helpAction = QAction(app.translate("MenuHelp", "Help"), widget)
helpAction.setShortcut("F1")
helpAction.setStatusTip(app.translate("HelpTip", "How to use this app"))
widget.connect(helpAction, SIGNAL("triggered()"), showHelp)
help_menu.addAction(helpAction)
help_menu.addSeparator()

# Create ABOUT window
aboutWindow = QWidget()
aboutWindow.setMinimumSize(320, 270)
aboutWindow.setMaximumSize(320, 270)
aboutWindow.setWindowFlags(Qt.WindowStaysOnTopHint)
aboutWindow.setWindowFlags(Qt.WindowCloseButtonHint)
aboutWindow.setWindowTitle(app.translate("MenuAbout", "About"))

aboutLogo = QLabel(parent=aboutWindow)
aboutLogo.setGeometry(15, 75, 90, 85)
aboutLogo.setPixmap(QPixmap(":/logo.png"))

aboutAppName = QLabel(app.translate("AppTitle", "DEMD database")+" v"+version,
                      parent=aboutWindow)
aboutAppName.setGeometry(10, 15, 300, 20)
aboutAppName.setAlignment(Qt.AlignCenter)
aboutAppName.setFont(QFont("", weight=QFont.Bold))

aboutDescription = QLabel(app.translate("AppDescription",
                                        "GUI wrapper for DEMD tools"),
                          parent=aboutWindow)
aboutDescription.setGeometry(10, 40, 300, 20)
aboutDescription.setAlignment(Qt.AlignCenter)

devs = ""
for line in developers[:-1]:
    devs += line + ", "
devs += developers[-1]
aboutDevelopersText = app.translate("AppDevelopersLicenses",
                                    "App and tools development:\n{:} and others\n\nLicensed by MIT license\nPySide under LGPL 3\nAll other components under their own licenses")
aboutDevelopers = QLabel(aboutDevelopersText.format(devs),
                         parent=aboutWindow)
aboutDevelopers.setWordWrap(True)
aboutDevelopers.setGeometry(120, 70, 195, 135)
aboutDevelopers.setAlignment(Qt.AlignTop)

aboutClose = QPushButton(app.translate("Close", "Close"), parent=aboutWindow)
aboutClose.setGeometry(70, 230, 180, 30)
aboutClose.clicked.connect(aboutWindow.close)
aboutClose.setFocus()

def showAbout():
    aboutWindow.show()

# Add about window
aboutAction = QAction(app.translate("MenuAbout", "About"), widget)
aboutAction.setStatusTip(app.translate("AboutTip",
                                       "App developers and licenses"))
widget.connect(aboutAction, SIGNAL("triggered()"), showAbout)
help_menu.addAction(aboutAction)

# App start
widget.show()

if first_launch:
    showHelp()

sys.exit(app.exec_())
