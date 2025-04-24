import json
from api_ollama import img_to_txt

def split_string(input_string, chunk_size):
    words = input_string.split()  # 把输入字符串按空格拆分成单词
    result = []
    current_chunk = ""  # 当前块的内容
    for word in words:
        # 如果当前块加上当前单词超过了 chunk_size，就把当前块放入结果
        if len(current_chunk) + len(word) + 1 > chunk_size:  # +1 是为了加上空格
            result.append(current_chunk)
            current_chunk = word  # 开始一个新的块
        else:
            if current_chunk:  # 如果当前块非空，先加一个空格再加单词
                current_chunk += " " + word
            else:
                current_chunk = word  # 如果当前块为空，直接加入单词

    # 如果有剩余的块，加入到结果中
    if current_chunk:
        result.append(current_chunk)

    return result



with open("output/kilosort论文_content_list.json", encoding="utf-8") as f:
    data = json.load(f)


# s是最终给处理好的字符串
s = ""

#############
chunk_size = 512
#############

#记录前一个item，以便回退
pre_item = {}
i = 0
while i < len(data):
    # print(i, data[i].get("type"))
    item = data[i]
    i += 1
    kind = item.get("type", "")
    if kind == "text":
        if item.get("text_level") == 1:#处理大标题的情况,默认情况下，大标题的字数会很少，不会超过token_limit，所以不用特判
            # print(222222222222222222222222)
            # break
            temp = "这是一个大标题:" + item.get("text")
            j = i
            while j < len(data):  #大标题后面尽量凑齐一整段block
                #避免重复遍历,i一定是j后面的元素
                i = j + 1
                #处理第一次进入循环的情况
                pre_item = item
                item = data[j]
                inner_kind = item.get("type", "")
                if inner_kind == "image" or inner_kind == "table":
                    img_path = item.get("img_path")
                    img_path = "output/" + img_path
                    # 保证图片不会超出token_limit
                    response = img_to_txt(img_path, chunk_size)
                    temp += "\n" + response + "\n"
                    #如果长度超出或者本身就是一个大标题，则break
                if len(temp) > chunk_size or item.get("text_level", "") == 1:

                    #向前回溯一个
                    i -= 1
                    # data = iter([pre_item] + list(data))
                    #直接break即可，因为现在的i就是要遍历的
                    break
                else:
                    temp += "\n" + data[j].get("text") + "\n"


            #处理最后可能没有push的temp
            if temp != "":
                s += temp + "\n" + "##########################################################################" + "\n"

        else:
            content = item.get("text", "")
            if len(content) > chunk_size:
                #如果大于token_limit，则进行分段
                list = split_string(content, chunk_size)
                s += '\n##########################################################################\n'.join(list)

            else:
                #否则就是一段正常文本
                s += item.get("text") + "\n" + "##########################################################################" + "\n"
    elif kind == "image":#普通图片
        img_path = item.get("img_path")
        img_path = "output/" + img_path
        # 保证图片不会超出token_limit
        response = img_to_txt(img_path, chunk_size)
        #   多个#是为了后续做rag的时候进行block切分
        s += response + "\n" + "##########################################################################" + "\n"

    elif kind == "table":#表格图片,同时解析表格内容
        img_path = item.get("img_path")
        img_path = "output/" + img_path
        response = img_to_txt(img_path, chunk_size)
        s += response + "\n" + "##########################################################################" + "\n"

    elif kind == "equation":#latex公式
        #设置算法思路，如果他是一个公式的话，那么他自己的相关性一定很差，必须往下配上一段文本弄在一起并合并成一个block
        temp = item.get("text")
        j = i
        while j < len(data):
            #暂时认为一个公式后面不会出现图片的情况

            #i一定是j后面的一个元素
            i = j + 1
            inner_kind = data[j].get("type", "")

            if inner_kind == "text":
                s += temp +  data[j].get("text") + "\n" + "##########################################################################" + "\n"
                break
            elif inner_kind == "equation":
                #debug
                # if j.get("text") == "":
                #shei     print(j)
                temp += "\n" + data[j].get("text") + "\n"
            j += 1

print(s)
with open(r"C:\Users\luyan\LightRAG\pdf_data.txt", "w", encoding="utf-8") as f:
    f.write(s)





