import os
import json
import re
from markdown_it import MarkdownIt
from markdown_it.token import Token
# Import the plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
# from mdit_py_plugins.amsmath import amsmath_plugin # Keep for potential future use

# --- Configuration ---
markdown_file_name = "output/kilosort论文.md"  # <<<--- 替换成你的 Markdown 文件路径
output_base_dir = "output_from_md"        # <<<--- 输出 JSON 的目录
default_page_idx = 0                     # Default page index for all elements
DEBUG_TOKENS = False                     # <<<--- Set to True to print all tokens

# --- Preparation ---
if not markdown_file_name or not os.path.exists(markdown_file_name):
    print(f"错误：Markdown 文件 '{markdown_file_name}' 不存在或未指定。")
    exit(1)

name_without_suff = os.path.splitext(os.path.basename(markdown_file_name))[0]

# Define output directory and filename
local_output_dir = os.path.join(output_base_dir, name_without_suff)
output_json_filename = f"{name_without_suff}_structure.json"
output_json_filepath = os.path.join(local_output_dir, output_json_filename)

# Create output directory
os.makedirs(local_output_dir, exist_ok=True)

print(f"输入 Markdown: {markdown_file_name}")
print(f"输出目录: {local_output_dir}")

# --- Helper function to finalize text block ---
def finalize_text_block(text_content, text_level=None):
    """Creates a text block dictionary if content exists."""
    stripped_content = text_content.strip()
    if not stripped_content:
        return None
    block = {"type": "text", "text": stripped_content, "page_idx": default_page_idx}
    if text_level is not None:
        block["text_level"] = text_level
    # print(f"  >> Finalizing text block: {block}") # Debugging
    return block

# --- Markdown Parsing and JSON Generation ---
try:
    # Read Markdown content
    print("正在读取 Markdown 文件...")
    with open(markdown_file_name, 'r', encoding='utf-8') as f:
        # Normalize line endings just in case
        md_content = f.read().replace('\r\n', '\n')
        md_lines = md_content.splitlines()
    print("Markdown 文件读取成功。")

    # Initialize Markdown parser - Start simpler, enable features needed
    # Using 'default' might be less restrictive than 'commonmark' sometimes
    md_parser = MarkdownIt() # Try 'default' preset
    md_parser.options['html'] = True # Allow HTML for tables later
    md_parser.enable('table')

    # *** Use the dollarmath plugin ***
    # Ensure allow_space is True if spaces can occur like '$$ ... $$'
    md_parser.use(dollarmath_plugin, allow_space=True)
    # md_parser.use(amsmath_plugin) # If needed for specific environments

    # Parse the Markdown content into a token stream
    print("正在解析 Markdown 内容...")
    tokens = md_parser.parse(md_content)
    print("Markdown 解析完成。")

    if DEBUG_TOKENS:
        print("--- Tokens ---")
        for idx, t in enumerate(tokens): print(f"{idx}: {t}")
        print("--------------")


    # --- Convert token stream to the target JSON structure ---
    results = []
    current_text_content = ""
    current_heading_level = None
    list_level = 0
    # No need for in_list_item flag if handling is within loop

    print("正在将解析结果转换为 JSON 结构...")

    i = 0
    while i < len(tokens):
        token = tokens[i]
        # print(f"Processing token {i}: {token.type} (Level: {token.level}, Tag: {token.tag})") # Detailed Debugging

        # --- Finalize Preceding Text ---
        # Decide if the *current* token marks the start of a block
        # that should finalize any pending inline text.
        # This includes block math, fences, tables, headings, lists, etc.
        should_finalize_text = False
        if token.type in ['math_block', 'fence', 'table_open', 'hr',
                          'heading_open', 'blockquote_open',
                          'bullet_list_open', 'ordered_list_open']:
            should_finalize_text = True
        # Also finalize if a paragraph starts *after* some content has been processed
        elif token.type == 'paragraph_open' and current_text_content:
             should_finalize_text = True

        if should_finalize_text and current_text_content:
            # print(f"  >> Finalizing text before token {i} ({token.type})") # Debugging
            block = finalize_text_block(current_text_content, current_heading_level)
            if block: results.append(block)
            current_text_content = ""
            # Only reset heading level if the new block isn't itself a heading continuation
            if token.type != 'heading_open':
                 current_heading_level = None


        # --- Process Current Token ---
        if token.type == 'heading_open':
            current_heading_level = int(token.tag[1]) # h1 -> 1
        elif token.type == 'bullet_list_open' or token.type == 'ordered_list_open':
             list_level += 1
        # list_item_open doesn't need special action if content is handled by inline

        elif token.type == 'table_open':
            # --- Table Handling (ensure it doesn't clash with finalize logic) ---
            table_start_line = token.map[0] if token.map else -1
            table_end_line = -1
            table_nesting = 0
            j = i + 1 # Start looking for close from next token
            while j < len(tokens):
                if tokens[j].type == "table_open": table_nesting += 1
                elif tokens[j].type == "table_close":
                    if table_nesting == 0:
                        table_end_line = tokens[j].map[1] if tokens[j].map else -1
                        break
                    else: table_nesting -= 1
                j += 1

            if table_start_line != -1 and table_end_line != -1:
                raw_table_md = "\n".join(md_lines[table_start_line:table_end_line])
                # Use a clean parser instance for rendering to avoid state issues
                table_html = MarkdownIt(html=True).enable('table').render(raw_table_md)
                table_block = {
                    "type": "table", "img_path": None, "table_caption": [],
                    "table_footnote": [], "table_body": table_html,
                    "page_idx": default_page_idx
                }
                results.append(table_block)
                i = j # Jump loop past the processed table tokens
            else:
                print(f"Warning: Could not parse table starting near line {table_start_line+1}")
                # Need to advance 'i' manually if table fails to parse to avoid infinite loop
                i += 1
            continue # Skip rest of loop for this iteration after handling table

        elif token.type == "inline":
            # Process children for text, images, inline math etc.
            for child in token.children:
                if child.type == 'text':
                    current_text_content += child.content
                elif child.type == 'softbreak': current_text_content += ' '
                elif child.type == 'hardbreak': current_text_content += '\n'
                elif child.type == 'image':
                    # Finalize preceding text *within* the inline context
                    if current_text_content:
                        block = finalize_text_block(current_text_content, current_heading_level)
                        if block: results.append(block)
                    current_text_content = "" # Reset for text after image
                    # Don't reset heading level here, image is inline with text potentially

                    # Create image block
                    alt_text = child.content
                    img_block = { "type": "image", "img_path": child.attrs.get('src', ''),
                                  "text": alt_text, "page_idx": default_page_idx }
                    results.append(img_block)
                elif child.type == 'math_inline':
                     current_text_content += f"${child.content}$"
                # ... (handle links etc.) ...

        elif token.type == "fence":
            # Text finalized before this block type
            language = token.info.lower().strip()
            content = token.content
            if language in ["latex", "math", "tex"]:
                 # Format fenced block as equation
                 if not (content.strip().startswith("$$") or content.strip().startswith("\\[")):
                      content = f"$$\n{content.strip()}\n$$"
                 else: content = content.strip() # Use content as is if delimiters present
                 results.append({ "type": "equation", "text": content,
                                  "text_format": "latex", "page_idx": default_page_idx })
            else: # Other code blocks as text
                 results.append({ "type": "text", "text": content, "page_idx": default_page_idx })

        # *** Handle math_block tokens from dollarmath plugin ***
        elif token.type == 'math_block':
            # Text finalized before this block type
            # print(f"  >> Found math_block: Content='{token.content}'") # Debugging
            content = token.content # Raw formula
            # Add delimiters for the JSON output
            formatted_content = f"$$\n{content.strip()}\n$$"
            results.append({ "type": "equation", "text": formatted_content,
                             "text_format": "latex", "page_idx": default_page_idx })

        # --- Handle Block Ends ---
        elif token.type.endswith("_close"):
            block_type = token.type.replace("_close", "")

            # Finalize text when major blocks close, if not already done
            if block_type in ["paragraph", "heading", "blockquote"]:
                 if current_text_content:
                    block = finalize_text_block(current_text_content, current_heading_level)
                    if block: results.append(block)
                 current_text_content = ""
                 current_heading_level = None # Reset heading level after block closes
            elif block_type == "list_item":
                 # List items often contain paragraphs implicitly, finalize text at item close
                 if current_text_content:
                    block = finalize_text_block(current_text_content) # No heading level
                    if block: results.append(block)
                 current_text_content = ""
            elif block_type in ["bullet_list", "ordered_list"]:
                 if list_level > 0: list_level -= 1

        # --- Advance ---
        # This needs careful handling, especially after table processing
        if token.type != 'table_open': # Avoid double increment if table was processed
            i += 1


    # Final check for any remaining text after the loop
    if current_text_content:
        block = finalize_text_block(current_text_content, current_heading_level)
        if block: results.append(block)

    print("JSON 结构生成完成。")

    # --- Save the structured JSON ---
    print(f"正在保存 JSON 文件至: {output_json_filepath}")
    with open(output_json_filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("JSON 文件保存成功。")

    print("\n处理完成！")


except ImportError as e:
    print(f"\n错误：缺少必要的包: {e}")
    print("请确保已安装 'markdown-it-py' 和 'mdit_py_plugins' (pip install markdown-it-py mdit_py_plugins)")
    exit(1)
except FileNotFoundError:
     print(f"错误：输入 Markdown 文件未找到: {markdown_file_name}")
     exit(1)
except Exception as e:
    import traceback
    print("\n--- 处理 Markdown 时发生错误 ---")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {e}")
    print("详细追溯信息:")
    traceback.print_exc()
    print("------------------")
    exit(1)