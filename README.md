# 此项目是专门针对于rag流程中的数据预处理截阶段，可以处理pdf，markdow格式里面的大多数数据类型，比如image，latex，table，text等等

[注：如果需要使用gpu进行推理加速，可以访问mineru官方项目进行环境配置](https://github.com/opendatalab/MinerU)
环境配置流程：

1. git clone https://github.com/HUY5877/Mineru_rag_data.git

2.创建conda环境，安装相应的包
``` bash
  conda env create -f environment.yml
```

## 操作流程：

# 注：在json_to_text文件中，你可以修改chunk_size,以及split_character #
### 处理pdf文件：

1.进入trans_pdf.py，修改pdf_file_name为你需要处理的pdf文件地址并运行该文件

2.此时会输出一个output文件夹，里面存有json，markdown，pdf等格式的文件，我们需要找出其中后缀名为content_list.json的文件，并记住该文件的地址

3.进入json_to_text文件，修改文件打开地址，同时修改输出文件地址，即可开始处理数据，
  ![image](https://github.com/user-attachments/assets/2ab8a8db-354d-499f-ac74-ff07ccf2e7a0)
  ![image](https://github.com/user-attachments/assets/3e137315-68d8-4b7d-99fb-45eee9cc159a)

### 处理markdown文件：

1.进入trans_markdown.py,修改输入文件地址和输出文件地址并运行
![image](https://github.com/user-attachments/assets/321dbe71-ebb9-488f-a7c2-183a52a18935)

![image](https://github.com/user-attachments/assets/a488c8ff-b552-44b8-8098-aa5fb1b0f7b9)

2.运行出来后会得到一个output_from_md文件夹，里面会有一个json文件，该json文件跟处理pdf生成的json文件格式类似

3.此时跟处理pdf文件的第3步相同


