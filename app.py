# app.py

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io

def gerar_imagem_etiqueta(codigo_produto, localizacao):
    """
    Gera a imagem da etiqueta na horizontal e a rotaciona em 90 graus no final
    para impressão em impressoras de rolo verticais.
    """
    # --- Configurações da Etiqueta (criada na horizontal: 8x4 cm) ---
    LARGURA_CM, ALTURA_CM, DPI = 8, 4, 300
    largura_px = int(LARGURA_CM / 2.54 * DPI)
    altura_px = int(ALTURA_CM / 2.54 * DPI)
    COR_FUNDO, COR_TEXTO = "white", "black"

    # --- Fontes (Carregando a partir da pasta 'fonts/') ---
    try:
        fonte_grande = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", size=160)
        fonte_pequena = ImageFont.truetype("fonts/DejaVuSans.ttf", size=45)
    except IOError:
        st.error("ERRO: Arquivos de fonte não encontrados na pasta 'fonts/'.")
        fonte_grande = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()

    # --- Criação da Imagem Base (na horizontal) ---
    etiqueta = Image.new('RGB', (largura_px, altura_px), COR_FUNDO)
    draw = ImageDraw.Draw(etiqueta)

    # --- Desenho dos elementos (na horizontal) ---
    pos_y_atual = 20
    # 1. Código do Produto
    bbox_codigo = draw.textbbox((0, 0), codigo_produto, font=fonte_grande)
    pos_x_codigo = (largura_px - (bbox_codigo[2] - bbox_codigo[0])) / 2
    draw.text((pos_x_codigo, pos_y_atual), codigo_produto, fill=COR_TEXTO, font=fonte_grande)
    pos_y_atual += (bbox_codigo[3] - bbox_codigo[1]) + 20
    # 2. Código de Barras
    barcode_class = barcode.get_barcode_class('code128')
    barcode_options = {'module_height': 10.0, 'write_text': False, 'quiet_zone': 2}
    barcode_obj = barcode_class(localizacao, writer=ImageWriter())
    buffer_barcode = io.BytesIO()
    barcode_obj.write(buffer_barcode, options=barcode_options)
    buffer_barcode.seek(0)
    barcode_img = Image.open(buffer_barcode)
    barcode_largura_desejada = int(largura_px * 0.9)
    ratio = barcode_largura_desejada / barcode_img.width
    barcode_img = barcode_img.resize((barcode_largura_desejada, int(barcode_img.height * ratio)))
    pos_x_barcode = int((largura_px - barcode_img.width) / 2)
    etiqueta.paste(barcode_img, (pos_x_barcode, pos_y_atual))
    pos_y_atual += barcode_img.height + 15
    # 3. Texto da Localização
    bbox_local = draw.textbbox((0, 0), localizacao, font=fonte_pequena)
    pos_x_local = (largura_px - (bbox_local[2] - bbox_local[0])) / 2
    draw.text((pos_x_local, pos_y_atual), localizacao, fill=COR_TEXTO, font=fonte_pequena)

    # --- ROTAÇÃO DA ETIQUETA ---
    # Rotaciona a imagem em 90 graus no sentido anti-horário.
    # expand=True garante que a nova imagem tenha o tamanho para caber a rotação.
    etiqueta_rotacionada = etiqueta.rotate(90, expand=True)

    # --- Salva a imagem ROTACIONADA em um buffer de bytes ---
    buffer_final = io.BytesIO()
    etiqueta_rotacionada.save(buffer_final, format="PNG")
    buffer_final.seek(0)
    
    return buffer_final

# --- Interface do Usuário Simplificada ---

st.set_page_config(page_title="Gerador de Etiquetas", layout="centered")

st.title("Gerador de Etiquetas de Armazém")

codigo_produto = st.text_input("1. Digite o Código do Produto", placeholder="Ex: 69")
localizacao = st.text_input("2. Digite a Localização", placeholder="Ex: P06-C2-A2-G11")

if st.button("Gerar Etiqueta"):
    if codigo_produto and localizacao:
        # Armazena os dados gerados no estado da sessão
        st.session_state.imagem_bytes = gerar_imagem_etiqueta(codigo_produto, localizacao)
        st.session_state.nome_arquivo = f"etiqueta_{codigo_produto.replace('/', '-')}_{localizacao.replace('/', '-')}.png"
    else:
        st.error("Por favor, preencha ambos os campos para gerar a etiqueta.")

# Mostra a pré-visualização e o botão de download se uma imagem já foi gerada
if 'imagem_bytes' in st.session_state:
    st.image(st.session_state.imagem_bytes, caption="Pré-visualização da Etiqueta (Rotacionada)")
    
    st.download_button(
        label="Baixar Etiqueta Rotacionada (.png)",
        data=st.session_state.imagem_bytes,
        file_name=st.session_state.nome_arquivo,
        mime="image/png"
    )
