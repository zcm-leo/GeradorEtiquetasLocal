# app.py

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io

def gerar_imagem_etiqueta(codigo_produto, localizacao):
    """
    Gera a imagem de 8x6 cm, posiciona os textos no topo e na base, e maximiza
    a altura do código de barras para preencher o espaço intermediário.
    """
    # --- Configurações da Etiqueta (8x6 cm) ---
    LARGURA_CM, ALTURA_CM, DPI = 8, 6, 300
    largura_px = int(LARGURA_CM / 2.54 * DPI)
    altura_px = int(ALTURA_CM / 2.54 * DPI)
    COR_FUNDO, COR_TEXTO = "white", "black"
    
    # --- Margens e Espaçamento ---
    margem_px = int(0.25 / 2.54 * DPI)
    # Espaço fixo entre o texto e o barcode
    padding_vertical = 20

    # --- Fontes ---
    try:
        fonte_grande = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", size=150)
        fonte_pequena = ImageFont.truetype("fonts/DejaVuSans.ttf", size=40)
    except IOError:
        st.error("ERRO: Arquivos de fonte não encontrados na pasta 'fonts/'.")
        fonte_grande = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()

    # --- Passo 1: Medir e Posicionar os Textos (Topo e Base) ---
    etiqueta = Image.new('RGB', (largura_px, altura_px), COR_FUNDO)
    draw = ImageDraw.Draw(etiqueta)

    # Medir e desenhar o código do produto no topo
    bbox_codigo = draw.textbbox((0, 0), codigo_produto, font=fonte_grande)
    altura_codigo = bbox_codigo[3] - bbox_codigo[1]
    pos_x_codigo = (largura_px - (bbox_codigo[2] - bbox_codigo[0])) / 2
    pos_y_codigo = margem_px + 10
    draw.text((pos_x_codigo, pos_y_codigo), codigo_produto, fill=COR_TEXTO, font=fonte_grande)

    # Medir e desenhar o texto da localização na base
    bbox_local = draw.textbbox((0, 0), localizacao, font=fonte_pequena)
    altura_local = bbox_local[3] - bbox_local[1]
    pos_x_local = (largura_px - (bbox_local[2] - bbox_local[0])) / 2
    pos_y_local = altura_px - margem_px - altura_local
    draw.text((pos_x_local, pos_y_local), localizacao, fill=COR_TEXTO, font=fonte_pequena)

    # --- Passo 2: Calcular o Espaço Disponível e Gerar o Barcode ---
    
    # Ponto Y onde o barcode começa (abaixo do código do produto)
    barcode_top_y = pos_y_codigo + altura_codigo + padding_vertical
    # Ponto Y onde o barcode termina (acima do texto da localização)
    barcode_bottom_y = pos_y_local - padding_vertical
    
    # Altura e largura exatas para o barcode
    barcode_final_height = barcode_bottom_y - barcode_top_y
    barcode_final_width = int((largura_px - 2 * margem_px) * 0.9)

    # Gerar o barcode com uma altura padrão
    barcode_class = barcode.get_barcode_class('code39')
    barcode_options = {'module_height': 15.0, 'write_text': False, 'add_checksum': False}
    localizacao_maiuscula = localizacao.upper()
    barcode_obj = barcode_class(localizacao_maiuscula, writer=ImageWriter())
    
    buffer_barcode = io.BytesIO()
    barcode_obj.write(buffer_barcode, options=barcode_options)
    buffer_barcode.seek(0)
    barcode_img = Image.open(buffer_barcode)
    
    # Redimensionar o barcode para as dimensões exatas calculadas
    barcode_img_redimensionada = barcode_img.resize((int(barcode_final_width), int(barcode_final_height)))
    
    # Colar o barcode redimensionado na posição correta
    pos_x_barcode = int((largura_px - barcode_img_redimensionada.width) / 2)
    etiqueta.paste(barcode_img_redimensionada, (pos_x_barcode, int(barcode_top_y)))

    # --- ROTAÇÃO DA ETIQUETA ---
    etiqueta_rotacionada = etiqueta.rotate(90, expand=True)

    # --- Salva a imagem ROTACIONADA em um buffer de bytes ---
    buffer_final = io.BytesIO()
    etiqueta_rotacionada.save(buffer_final, format="PNG")
    buffer_final.seek(0)
    
    return buffer_final

# --- Interface do Usuário (sem alterações) ---
st.set_page_config(page_title="Gerador de Etiquetas", layout="centered")
st.title("Gerador de Etiquetas de Armazém")
codigo_produto = st.text_input("1. Digite o Código do Produto", placeholder="Ex: 11522")
localizacao = st.text_input("2. Digite a Localização", placeholder="Ex: P06-C2-A2-G11")

if st.button("Gerar Etiqueta"):
    if codigo_produto and localizacao:
        st.session_state.imagem_bytes = gerar_imagem_etiqueta(codigo_produto, localizacao)
        st.session_state.nome_arquivo = f"etiqueta_{codigo_produto.replace('/', '-')}_{localizacao.replace('/', '-')}.png"
    else:
        st.error("Por favor, preencha ambos os campos para gerar a etiqueta.")

if 'imagem_bytes' in st.session_state:
    st.image(st.session_state.imagem_bytes, caption="Pré-visualização da Etiqueta (6x8 cm)")
    st.download_button(
        label="Baixar Etiqueta 6x8 (.png)",
        data=st.session_state.imagem_bytes,
        file_name=st.session_state.nome_arquivo,
        mime="image/png"
    )
