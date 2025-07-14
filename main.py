import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import pandas as pd
import webbrowser
from datetime import datetime
import os
import json
from PIL import Image

DB_FILE = "coletas.db"
EXCEL_FILE = "coletas.xlsx"
CONFIG_FILE = "config.json"

# ---------------------- TEMA ----------------------
def carregar_tema():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            tema = config.get("tema", "dark")
            ctk.set_appearance_mode(tema)
    else:
        ctk.set_appearance_mode("dark")

# ---------------------- BANCO ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS coletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quem_pediu TEXT, telefone_pedido TEXT, endereco_coleta TEXT,
        quantos_volumes TEXT, peso TEXT, valor_nf TEXT,
        endereco_entrega TEXT, destinatario TEXT, telefone_destinatario TEXT,
        motorista TEXT, telefone_motorista TEXT,
        data_envio TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS motoristas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, telefone TEXT
    )''')
    conn.commit()
    conn.close()

def obter_motoristas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, telefone FROM motoristas ORDER BY nome ASC")
    motoristas = cursor.fetchall()
    conn.close()
    return motoristas

def salvar_coleta(dados):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO coletas (
        quem_pediu, telefone_pedido, endereco_coleta, quantos_volumes,
        peso, valor_nf, endereco_entrega, destinatario, telefone_destinatario,
        motorista, telefone_motorista, data_envio
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (
        dados["quem_pediu"], dados["telefone_pedido"], dados["endereco_coleta"],
        dados["quantos_volumes"], dados["peso"], dados["valor_nf"], dados["endereco_entrega"],
        dados["destinatario"], dados["telefone_destinatario"], dados["motorista"],
        dados["telefone_motorista"], dados["data_envio"]
    ))
    conn.commit()
    conn.close()

def cadastrar_motorista(nome, telefone):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO motoristas (nome, telefone) VALUES (?, ?)", (nome, telefone))
    conn.commit()
    conn.close()

def excluir_motorista(nome):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM motoristas WHERE nome = ?", (nome,))
    conn.commit()
    conn.close()

# ---------------------- FRAME SCROLL ----------------------
class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

# ---------------------- APP PRINCIPAL ----------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Formulário de Coleta - Ávila DevOps")
        self.geometry("780x720")
        self.minsize(600, 600)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        init_db()
        self.campos = {}
        self.motoristas = {}

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.criar_widgets(self.scroll_frame)

        self.rodape = ctk.CTkLabel(self, text="Desenvolvido por Nícolas Ávila", font=("Segoe UI", 8), text_color="#888888")
        self.rodape.grid(row=1, column=0, sticky="e", padx=10, pady=(0,10))

        self.adicionar_engrenagem()

    def criar_widgets(self, master):
        row = 0

        def campo(label, chave):
            nonlocal row
            ctk.CTkLabel(master, text=label).grid(row=row, column=0, sticky="w", pady=6)
            entry = ctk.CTkEntry(master)
            entry.grid(row=row, column=1, sticky="ew", pady=6, padx=(10,0))
            self.campos[chave] = entry
            row += 1

        campo("Quem pediu a coleta?", "quem_pediu")
        campo("Telefone de quem pediu", "telefone_pedido")

        # Endereço da coleta
        ctk.CTkLabel(master, text="Endereço da coleta").grid(row=row, column=0, sticky="w", pady=6)
        frame_endereco = ctk.CTkFrame(master, fg_color="transparent")
        frame_endereco.grid(row=row, column=1, sticky="ew", pady=6, padx=(10,0))
        frame_endereco.grid_columnconfigure(0, weight=1)

        entry_coleta = ctk.CTkEntry(frame_endereco)
        entry_coleta.grid(row=0, column=0, sticky="ew")
        btn_maps = ctk.CTkButton(frame_endereco, text="🔎 Maps", width=80, command=lambda: self.abrir_maps(entry_coleta))
        btn_maps.grid(row=0, column=1, padx=(10,0))
        self.campos["endereco_coleta"] = entry_coleta
        row += 1

        campo("Quantos volumes?", "quantos_volumes")
        campo("Peso total (kg)", "peso")
        campo("Valor do produto/NF", "valor_nf")

        # Endereço da entrega
        ctk.CTkLabel(master, text="Endereço da entrega").grid(row=row, column=0, sticky="w", pady=6)
        frame_entrega = ctk.CTkFrame(master, fg_color="transparent")
        frame_entrega.grid(row=row, column=1, sticky="ew", pady=6, padx=(10,0))
        frame_entrega.grid_columnconfigure(0, weight=1)

        entry_entrega = ctk.CTkEntry(frame_entrega)
        entry_entrega.grid(row=0, column=0, sticky="ew")
        btn_maps2 = ctk.CTkButton(frame_entrega, text="🔎 Maps", width=80, command=lambda: self.abrir_maps(entry_entrega))
        btn_maps2.grid(row=0, column=1, padx=(10,0))
        self.campos["endereco_entrega"] = entry_entrega
        row += 1

        campo("Nome do destinatário", "destinatario")
        campo("Telefone do destinatário", "telefone_destinatario")

        ctk.CTkLabel(master, text="Motorista").grid(row=row, column=0, sticky="w", pady=(20,6))
        self.combo_motorista = ctk.CTkComboBox(master, width=300)
        self.combo_motorista.grid(row=row, column=1, sticky="ew", pady=(20,6), padx=(10,0))
        self.atualizar_motoristas()
        row += 1

        btn_frame = ctk.CTkFrame(master, fg_color="transparent")
        btn_frame.grid(row=row, column=1, sticky="w", padx=(10,0))
        ctk.CTkButton(btn_frame, text="Cadastrar", width=100, command=self.cadastrar_motorista_dialog, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Excluir", width=100, command=self.excluir_motorista_dialog, fg_color="red").pack(side="left", padx=5)
        row += 1

        ctk.CTkButton(master, text="🚚 Enviar Coleta", font=("Segoe UI", 14, "bold"),
                      fg_color="#0a74da", hover_color="#095ab3", command=self.enviar_coleta).grid(row=row, column=1, sticky="e", pady=20, padx=(10,0))

    def abrir_maps(self, entry):
        endereco = entry.get().strip()
        if endereco:
            url = f"https://www.google.com/maps/search/{endereco.replace(' ', '+')}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Campo vazio", "Digite o endereço antes de pesquisar.")

    def atualizar_motoristas(self):
        dados = obter_motoristas()
        self.motoristas = {nome: tel for nome, tel in dados}
        self.combo_motorista.configure(values=list(self.motoristas.keys()))
        if self.motoristas:
            self.combo_motorista.set(list(self.motoristas.keys())[0])
        else:
            self.combo_motorista.set("")

    def cadastrar_motorista_dialog(self):
        nome = simpledialog.askstring("Cadastro de Motorista", "Nome:")
        telefone = simpledialog.askstring("Cadastro de Motorista", "WhatsApp:")
        if nome and telefone:
            cadastrar_motorista(nome, telefone)
            self.atualizar_motoristas()

    def excluir_motorista_dialog(self):
        nome = self.combo_motorista.get()
        if nome and nome in self.motoristas:
            excluir_motorista(nome)
            self.atualizar_motoristas()

    def enviar_coleta(self):
        dados = {k: v.get().strip() for k, v in self.campos.items()}
        if not all(dados.values()) or not self.combo_motorista.get():
            messagebox.showwarning("Erro", "Preencha todos os campos e selecione um motorista.")
            return

        motorista = self.combo_motorista.get()
        telefone = self.motoristas.get(motorista, "")

        dados["motorista"] = motorista
        dados["telefone_motorista"] = telefone
        dados["data_envio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        salvar_coleta(dados)

        msg = f"📦 *Nova Coleta* \n" \
              f"👤 Pedido por: {dados['quem_pediu']} ({dados['telefone_pedido']})\n" \
              f"📍 Coletar: {dados['endereco_coleta']}\n" \
              f"📦 Volumes: {dados['quantos_volumes']} - Peso: {dados['peso']}kg\n" \
              f"💰 Valor NF: R${dados['valor_nf']}\n" \
              f"📦 Entregar: {dados['endereco_entrega']}\n" \
              f"👤 Destinatário: {dados['destinatario']} ({dados['telefone_destinatario']})"

        url = f"https://wa.me/55{telefone}?text={msg.replace(' ', '%20').replace('\n', '%0A')}"
        webbrowser.open(url)

        messagebox.showinfo("Sucesso", "Coleta enviada com sucesso!")
        self.resetar_campos()

    def resetar_campos(self):
        for entry in self.campos.values():
            entry.delete(0, 'end')
        self.combo_motorista.set("")
        self.atualizar_motoristas()

    def adicionar_engrenagem(self):
        gear_path = os.path.join("assets", "gear.png")
        gear_img = ctk.CTkImage(Image.open(gear_path), size=(24, 24)) if os.path.exists(gear_path) else None
        self.btn_engrenagem = ctk.CTkButton(self, text="", image=gear_img, width=32, height=32,
                                            fg_color="transparent", hover_color="#333",
                                            command=self.mostrar_opcoes_tema)
        self.btn_engrenagem.place(relx=0.97, rely=0.01, anchor="ne")

        self.menu_tema = ctk.CTkOptionMenu(master=self,
                                           values=["Dark", "Light", "System"],
                                           command=self.trocar_tema,
                                           width=120)
        self.menu_tema.set(ctk.get_appearance_mode().capitalize())
        self.menu_tema.place_forget()
        self.theme_menu_visible = False

    def mostrar_opcoes_tema(self):
        if not self.theme_menu_visible:
            self.menu_tema.place(relx=0.81, rely=0.01)
        else:
            self.menu_tema.place_forget()
        self.theme_menu_visible = not self.theme_menu_visible

    def trocar_tema(self, mode):
        mode = mode.lower()
        ctk.set_appearance_mode(mode)
        self.menu_tema.place_forget()
        self.theme_menu_visible = False
        with open(CONFIG_FILE, "w") as f:
            json.dump({"tema": mode}, f)
        self.menu_tema.set(mode.capitalize())

# ---------------------- INÍCIO ----------------------
if __name__ == "__main__":
    carregar_tema()
    init_db()
    app = App()
    app.mainloop()
