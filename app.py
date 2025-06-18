# app.py

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import io

def gerar_imagem_etiqueta(codigo_produto, localizacao):
    """
    Gera a imagem de 8x6 cm, centraliza o conteúdo verticalmente dentro das margens,
    e a rotaciona em 90 graus para um resultado final de 6x8 cm.
    """
    # --- Configurações da Etiqueta (8x6 cm) ---
    LARGURA_CM, ALTURA_CM, DPI = 8, 6, 300
    largura_px = int(LARGURA_CM / 2.54 * DPI)
    altura_px = int(ALTURA_CM / 2.54 * DPI)
    COR_FUNDO, COR_TEXTO = "white", "black"
    
    # --- Margens Internas ---
    margem_px = int(0.25 / 2.54 * DPI)

    # --- Fontes ---
    try:
        fonte_grande = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", size=150)
        fonte_pequena = ImageFont.truetype("fonts/DejaVuSans.ttf", size=40)
    except IOError:
        st.error("ERRO: Arquivos de fonte não encontrados na pasta 'fonts/'.")
        fonte_grande = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()

    # --- Passo 1: MEDIR a altura de todos os elementos primeiro ---
    temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1))) # Desenho temporário para medição

    # Medir texto do código
    bbox_codigo = temp_draw.textbbox((0, 0), codigo_produto, font=fonte_grande)
    altura_codigo = bbox_codigo[3] - bbox_codigo[1]

    # Gerar e medir o barcode
    barcode_class = barcode.get_barcode_class('code39')
    barcode_options = {'module_height': 9.0, 'write_text': False, 'add_checksum': False}
    localizacao_maiuscula = localizacao.upper()
    barcode_obj = barcode_class(localizacao_maiuscula, writer=ImageWriter())
    buffer_barcode = io.BytesIO()
    barcode_obj.write(buffer_barcode, options=barcode_options)
    buffer_barcode.seek(0)
    barcode_img = Image.open(buffer_barcode)
    safe_width = largura_px - (2 * margem_px)
    barcode_largura_desejada = int(safe_width * 0.9)
    ratio = barcode_largura_desejada / barcode_img.width
    barcode_img_redimensionada = barcode_img.resize((barcode_largura_desejada, int(barcode_img.height * ratio)))
    altura_barcode = barcode_img_redimensionada.height

    # Medir texto da localização
    bbox_local = temp_draw.textbbox((0, 0), localizacao, font=fonte_pequena)
    altura_local = bbox_local[3] - bbox_local[1]

    # --- Passo 2: CALCULAR o espaçamento dinâmico ---
    altura_total_conteudo = altura_codigo + altura_barcode + altura_local
    espaco_vertical_seguro = altura_px - (2 * margem_px)
    
    # O espaço em branco que sobra será dividido entre os 2 vãos (acima e abaixo do barcode)
    espacamento_entre_elementos = (espaco_vertical_seguro - altura_total_conteudo) / 2

    # --- Passo 3: DESENHAR a etiqueta final com o posicionamento calculado ---
    etiqueta = Image.new('RGB', (largura_px, altura_px), COR_FUNDO)
    draw = ImageDraw.Draw(etiqueta)

    # Posição Y inicial começa na margem superior
    pos_y_atual = margem_px

    # 1. Código do Produto
    pos_x_codigo = (largura_px - (bbox_codigo[2] - bbox_codigo[0])) / 2
    draw.text((pos_x_codigo, pos_y_atual), codigo_produto, fill=COR_TEXTO, font=fonte_grande)
    pos_y_atual += altura_codigo + espacamento_entre_elementos

    # 2. Código de Barras
    pos_x_barcode = int((largura_px - barcode_img_redimensionada.width) / 2)
    etiqueta.paste(barcode_img_redimensionada, (pos_x_barcode, int(pos_y_atual)))
    pos_y_atual += altura_barcode + espacamento_entre_elementos

    # 3. Texto da Localização
    pos_x_local = (largura_px - (bbox_local[2] - bbox_local[0])) / 2
    draw.text((pos_x_local, int(pos_y_atual)), localizacao, fill=COR_TEXTO, font=fonte_pequena)

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
