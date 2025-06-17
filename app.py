# app.py

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io

def gerar_imagem_etiqueta(codigo_produto, localizacao):
    """
    Gera a imagem da etiqueta com layout verticalmente compactado para garantir
    que todos os elementos fiquem visíveis.
    """
    # --- Configurações da Etiqueta ---
    LARGURA_CM, ALTURA_CM, DPI = 8, 4, 300
    largura_px = int(LARGURA_CM / 2.54 * DPI)
    altura_px = int(ALTURA_CM / 2.54 * DPI)
    COR_FUNDO, COR_TEXTO = "white", "black"

    # --- Fontes (Tenta usar Arial, senão usa a padrão) ---
    try:
        # --- AJUSTES DE FONTE ---
        fonte_grande = ImageFont.truetype("arialbd.ttf", size=120)
        fonte_pequena = ImageFont.truetype("arial.ttf", size=45)
    except IOError:
        st.warning("Fontes Arial não encontradas. Usando fontes padrão.")
        fonte_grande = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()

    # --- Criação da Imagem Base ---
    etiqueta = Image.new('RGB', (largura_px, altura_px), COR_FUNDO)
    draw = ImageDraw.Draw(etiqueta)

    # --- Desenho dos elementos com layout compacto ---
    pos_y_atual = 15 # Margem superior reduzida

    # 1. Código do Produto
    bbox_codigo = draw.textbbox((0, 0), codigo_produto, font=fonte_grande)
    pos_x_codigo = (largura_px - (bbox_codigo[2] - bbox_codigo[0])) / 2
    draw.text((pos_x_codigo, pos_y_atual), codigo_produto, fill=COR_TEXTO, font=fonte_grande)
    pos_y_atual += (bbox_codigo[3] - bbox_codigo[1]) + 15 # Espaçamento reduzido

    # 2. Código de Barras
    barcode_class = barcode.get_barcode_class('code128')
    # --- AJUSTE DE ALTURA DO BARCODE ---
    barcode_options = {'module_height': 10.0, 'write_text': False, 'quiet_zone': 2} # Reduzido de 12.0
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
    pos_y_atual += barcode_img.height + 10 # Espaçamento reduzido

    # 3. Texto da Localização
    bbox_local = draw.textbbox((0, 0), localizacao, font=fonte_pequena)
    pos_x_local = (largura_px - (bbox_local[2] - bbox_local[0])) / 2
    draw.text((pos_x_local, pos_y_atual), localizacao, fill=COR_TEXTO, font=fonte_pequena)

    # --- Salva a imagem final em um buffer de bytes ---
    buffer_final = io.BytesIO()
    etiqueta.save(buffer_final, format="PNG")
    buffer_final.seek(0)
    
    return buffer_final

# --- Interface do Usuário com Streamlit (sem alterações) ---

st.set_page_config(page_title="Gerador de Etiquetas", layout="centered")

st.title("Gerador de Etiquetas de Armazém")

codigo_produto = st.text_input("1. Digite o Código do Produto", placeholder="Ex: 69")
localizacao = st.text_input("2. Digite a Localização", placeholder="Ex: P06-C2-A2-G11")

if st.button("Gerar Etiqueta"):
    if codigo_produto and localizacao:
        imagem_bytes = gerar_imagem_etiqueta(codigo_produto, localizacao)
        st.success("Etiqueta gerada com sucesso!")
        st.image(imagem_bytes, caption="Pré-visualização da Etiqueta Gerada")
        
        nome_arquivo = f"etiqueta_{codigo_produto.replace('/', '-')}_{localizacao.replace('/', '-')}.png"
        st.download_button(
            label="Baixar Etiqueta (.png)",
            data=imagem_bytes,
            file_name=nome_arquivo,
            mime="image/png"
        )
    else:
        st.error("Por favor, preencha ambos os campos para gerar a etiqueta.")