# nano banana接口Gemini 原生格式

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1beta/models/{model}:generateContent:
    post:
      summary: nano banana接口Gemini 原生格式
      deprecated: false
      description: >
        # 图片生成接口文档（Gemini 原生格式）


        ## 接口地址

        `POST /v1beta/models/{model}:generateContent`


        ## 功能说明

        支持文生图和图生图两种模式的图片生成，使用 Gemini 原生格式接口，**同步返回**，无需轮询。


        图片通过 `candidates[].content.parts[].text` 字段以 Markdown 格式返回，根据模型不同有两种形式：

        - **1K 及以下模型**：返回 Google Cloud Storage 带签名临时
        URL，格式：`![image](https://storage.googleapis.com/...)`

        - **2K / 4K 模型**：返回 Base64
        内嵌图片，格式：`![image](data:image/jpeg;base64,...)`



        ## 支持的模型


        | model 参数（实际传入值） | 分辨率 | 宽高比 | 返回格式 |

        |------------------------|--------|--------|---------|

        | `nano_banana_2-portrait` | 标准 | 竖图 9:16 | URL 链接 |

        | `nano_banana_2-landscape` | 标准 | 横图 16:9 | URL 链接 |

        | `nano_banana_pro-1K-portrait` | 1K | 竖图 9:16 | URL 链接 |

        | `nano_banana_pro-1K-landscape` | 1K | 横图 16:9 | URL 链接 |

        | `nano_banana_pro-2K-portrait` | 2K | 竖图 9:16 | Base64 |

        | `nano_banana_pro-2K-landscape` | 2K | 横图 16:9 | Base64 |

        | `nano_banana_pro-4K-portrait` | 4K | 竖图 9:16 | Base64 |

        | `nano_banana_pro-4K-landscape` | 4K | 横图 16:9 | Base64 |


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 是 | application/json |


        ## 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | contents | array | 是 | 对话内容列表 |

        | contents[].role | string | 是 | 固定填 `"user"` |

        | contents[].parts | array | 是 | 内容部件数组，文生图只含 text，图生图含 inline_data +
        text |

        | contents[].parts[].text | string | 文生图必填 | 图片描述提示词，最大长度 10000 字符 |

        | contents[].parts[].inline_data | object | 图生图必填 | 参考图片对象 |

        | contents[].parts[].inline_data.mime_type | string | 是 |
        图片格式，如：`image/jpeg`、`image/png`、`image/webp` |

        | contents[].parts[].inline_data.data | string | 是 | 图片的纯 Base64
        字符串（**不含** `data:image/jpeg;base64,` 前缀） |

        | generationConfig | object | 否 | 生成配置 |

        | generationConfig.responseModalities | string[] | 否 | 响应模态，填
        `["IMAGE"]` 只返回图片，默认 `["TEXT","IMAGE"]` |


        ## 请求示例


        ### 文生图（横图 16:9）

        ```bash

        curl -X POST
        https://otuapi.com/v1beta/models/nano_banana_2-landscape:generateContent
        \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "contents": [
              {
                "role": "user",
                "parts": [
                  {
                    "text": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉"
                  }
                ]
              }
            ],
            "generationConfig": {
              "responseModalities": ["IMAGE"]
            }
          }'
        ```


        **请求体（JSON）：**

        ```json

        {
          "contents": [
            {
              "role": "user",
              "parts": [
                {
                  "text": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉"
                }
              ]
            }
          ],
          "generationConfig": {
            "responseModalities": ["IMAGE"]
          }
        }

        ```


        ### 文生图（竖图 9:16，高清 1K）

        ```bash

        curl -X POST
        https://otuapi.com/v1beta/models/nano_banana_pro-1K-portrait:generateContent
        \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "contents": [
              {
                "role": "user",
                "parts": [
                  {
                    "text": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉"
                  }
                ]
              }
            ],
            "generationConfig": {
              "responseModalities": ["IMAGE"]
            }
          }'
        ```


        ### 图生图（单张参考图，竖图 9:16）

        ```bash

        curl -X POST
        https://otuapi.com/v1beta/models/nano_banana_2-portrait:generateContent
        \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "contents": [
              {
                "role": "user",
                "parts": [
                  {
                    "inline_data": {
                      "mime_type": "image/jpeg",
                      "data": "/9j/4AAQSkZJRg..."
                    }
                  },
                  {
                    "text": "将这张图片转换成油画风格"
                  }
                ]
              }
            ],
            "generationConfig": {
              "responseModalities": ["IMAGE"]
            }
          }'
        ```


        ### 图生图（多张参考图，横图 16:9）

        ```json

        {
          "contents": [
            {
              "role": "user",
              "parts": [
                {
                  "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": "/9j/4AAQSkZJRg..."
                  }
                },
                {
                  "inline_data": {
                    "mime_type": "image/png",
                    "data": "iVBORw0KGgoAAAANSU..."
                  }
                },
                {
                  "text": "融合这两张图片的风格，生成一张新的风景图"
                }
              ]
            }
          ],
          "generationConfig": {
            "responseModalities": ["IMAGE"]
          }
        }

        ```


        > 💡 多张参考图示例使用模型 `nano_banana_2-landscape`，URL 路径为：

        > `POST /v1beta/models/nano_banana_2-landscape:generateContent`


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | candidates | array | 候选结果列表 |

        | candidates[].content.role | string | 固定值 `"model"` |

        | candidates[].content.parts | array | 内容部件数组 |

        | candidates[].content.parts[].text | string | 图片以 Markdown 格式内嵌：URL 模型为
        `![image](https://...)` ，Base64 模型为
        `![image](data:image/jpeg;base64,...)` |

        | candidates[].finishReason | string | 完成原因，正常为 `"STOP"` |

        | candidates[].index | number | 候选结果索引，从 0 开始 |

        | candidates[].safetyRatings | array | 安全评级列表 |

        | usageMetadata.promptTokenCount | number | 输入消耗的 token 数 |

        | usageMetadata.candidatesTokenCount | number | 输出消耗的 token 数 |

        | usageMetadata.totalTokenCount | number | 总消耗 token 数 |


        ## 响应示例


        ### 成功响应（1K 及以下模型 — 返回 URL 链接）

        ```json

        {
          "candidates": [
            {
              "content": {
                "role": "model",
                "parts": [
                  {
                    "text": "![image](https://storage.googleapis.com/ai-sandbox-videofx/image/xxxxxxxx?GoogleAccessId=...&Expires=...&Signature=...)\n\n"
                  }
                ]
              },
              "finishReason": "STOP",
              "index": 0,
              "safetyRatings": []
            }
          ],
          "usageMetadata": {
            "promptTokenCount": 31,
            "toolUsePromptTokenCount": 0,
            "candidatesTokenCount": 1003,
            "totalTokenCount": 1034,
            "thoughtsTokenCount": 0,
            "cachedContentTokenCount": 0,
            "promptTokensDetails": null,
            "toolUsePromptTokensDetails": null
          }
        }

        ```


        ### 成功响应（2K / 4K 模型 — 返回 Base64）

        ```json

        {
          "candidates": [
            {
              "content": {
                "role": "model",
                "parts": [
                  {
                    "text": "![image](data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/...base64数据...)\n\n"
                  }
                ]
              },
              "finishReason": "STOP",
              "index": 0,
              "safetyRatings": []
            }
          ],
          "usageMetadata": {
            "promptTokenCount": 31,
            "toolUsePromptTokenCount": 0,
            "candidatesTokenCount": 1110,
            "totalTokenCount": 1141,
            "thoughtsTokenCount": 0,
            "cachedContentTokenCount": 0,
            "promptTokensDetails": null,
            "toolUsePromptTokensDetails": null
          }
        }

        ```


        ## 提取图片方式


        图片统一内嵌在 `candidates[0].content.parts[0].text` 字段中，需用正则提取括号内的内容：


        ```

        正则：/!\[image\]\(([^)]+)\)/

        ```


        提取后根据内容判断类型：

        - 以 `https://` 开头 → 图片 URL，可直接用于 `<img src>` 或下载

        - 以 `data:image/` 开头 → Base64 Data URL，可直接用于 `<img src>` 展示，或解码后保存为文件


        示例（JavaScript）：

        ```javascript

        const text = response.candidates[0].content.parts[0].text;

        const match = text.match(/!\[image\]\(([^)]+)\)/);

        const imageContent = match ? match[1] : null;


        if (imageContent) {
          if (imageContent.startsWith('data:image/')) {
            // Base64 格式（2K/4K 模型）—— 可直接赋值给 img.src
            img.src = imageContent;
          } else {
            // URL 格式（1K 及以下模型）—— 临时链接，需及时下载
            img.src = imageContent;
          }
        }

        ```


        示例（Python）：

        ```python

        import re, base64


        text = response["candidates"][0]["content"]["parts"][0]["text"]

        match = re.search(r'!\[image\]\(([^)]+)\)', text)

        image_content = match.group(1) if match else None


        if image_content:
            if image_content.startswith('data:image/'):
                # Base64 格式（2K/4K 模型）
                header, b64data = image_content.split(',', 1)
                image_bytes = base64.b64decode(b64data)
                with open('output.jpg', 'wb') as f:
                    f.write(image_bytes)
            else:
                # URL 格式（1K 及以下模型）
                image_url = image_content
                # 使用 requests 下载或直接展示
        ```


        ## 注意事项


        1. **同步返回**：本接口为同步接口，图片生成完毕后一次性返回，无需轮询，请求耗时通常为 5~30 秒，请确保客户端超时时间设置足够长（建议
        120 秒）

        2. **宽高比控制**：宽高比通过**模型名称后缀**控制：
           - 加 `-portrait` → 竖图（9:16），如 `nano_banana_2-portrait`
           - 加 `-landscape` → 横图（16:9），如 `nano_banana_2-landscape`
        3. **返回格式差异**：
           - `nano_banana_2` / `nano_banana_pro` / `nano_banana_pro-1K` → 返回 **URL 链接**（Google Cloud Storage 临时链接，有效期较短，请及时下载）
           - `nano_banana_pro-2K` / `nano_banana_pro-4K` → 返回 **Base64 Data URL**，可直接用于展示
        4. **参考图片格式**：支持 `image/jpeg`、`image/png`、`image/webp`，单张最大 5MB

        5. **参考图片数量**：最多 14 张参考图片

        6. **任务模式**：
           - `parts` 中只有 `text` = 文生图模式
           - `parts` 中包含 `inline_data` + `text` = 图生图模式
      tags:
        - 失效接口
      parameters:
        - name: model
          in: path
          description: ''
          required: true
          example: nano_banana_2
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: true
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                contents:
                  type: array
                  items:
                    type: object
                    properties:
                      role:
                        type: string
                      parts:
                        type: array
                        items:
                          type: object
                          properties:
                            text:
                              type: string
                          x-apifox-orders:
                            - text
                          required:
                            - text
                    x-apifox-orders:
                      - role
                      - parts
                generationConfig:
                  type: object
                  properties:
                    responseModalities:
                      type: array
                      items:
                        type: string
                    imageConfig:
                      type: object
                      properties:
                        aspectRatio:
                          type: string
                        imageSize:
                          type: string
                      x-apifox-orders:
                        - aspectRatio
                        - imageSize
                  required:
                    - responseModalities
                  x-apifox-orders:
                    - responseModalities
                    - imageConfig
              required:
                - contents
                - generationConfig
              x-apifox-orders:
                - contents
                - generationConfig
            example:
              contents:
                - role: user
                  parts:
                    - text: 美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉
              generationConfig:
                responseModalities:
                  - IMAGE
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  candidates:
                    type: array
                    items:
                      type: object
                      properties:
                        content:
                          type: object
                          properties:
                            role:
                              type: string
                            parts:
                              type: array
                              items:
                                type: object
                                properties:
                                  text:
                                    type: string
                                  inline_data:
                                    type: object
                                    properties:
                                      mime_type:
                                        type: string
                                      data:
                                        type: string
                                    required:
                                      - mime_type
                                      - data
                                    x-apifox-orders:
                                      - mime_type
                                      - data
                                x-apifox-orders:
                                  - text
                                  - inline_data
                          required:
                            - role
                            - parts
                          x-apifox-orders:
                            - role
                            - parts
                        finishReason:
                          type: string
                        index:
                          type: integer
                        safetyRatings:
                          type: array
                          items:
                            type: string
                      x-apifox-orders:
                        - content
                        - finishReason
                        - index
                        - safetyRatings
                  usageMetadata:
                    type: object
                    properties:
                      promptTokenCount:
                        type: integer
                      toolUsePromptTokenCount:
                        type: integer
                      candidatesTokenCount:
                        type: integer
                      totalTokenCount:
                        type: integer
                      thoughtsTokenCount:
                        type: integer
                      cachedContentTokenCount:
                        type: integer
                      promptTokensDetails:
                        type: 'null'
                      toolUsePromptTokensDetails:
                        type: 'null'
                    required:
                      - promptTokenCount
                      - toolUsePromptTokenCount
                      - candidatesTokenCount
                      - totalTokenCount
                      - thoughtsTokenCount
                      - cachedContentTokenCount
                      - promptTokensDetails
                      - toolUsePromptTokensDetails
                    x-apifox-orders:
                      - promptTokenCount
                      - toolUsePromptTokenCount
                      - candidatesTokenCount
                      - totalTokenCount
                      - thoughtsTokenCount
                      - cachedContentTokenCount
                      - promptTokensDetails
                      - toolUsePromptTokensDetails
                required:
                  - candidates
                  - usageMetadata
                x-apifox-orders:
                  - candidates
                  - usageMetadata
              example:
                candidates:
                  - content:
                      role: model
                      parts:
                        - text: >+
                            ![image](https://storage.googleapis.com/ai-sandbox-videofx/image/xxxxxxxx?GoogleAccessId=...&Expires=...&Signature=...)

                    finishReason: STOP
                    index: 0
                    safetyRatings: []
                usageMetadata:
                  promptTokenCount: 31
                  toolUsePromptTokenCount: 0
                  candidatesTokenCount: 1003
                  totalTokenCount: 1034
                  thoughtsTokenCount: 0
                  cachedContentTokenCount: 0
                  promptTokensDetails: null
                  toolUsePromptTokensDetails: null
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 失效接口
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-426900205-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
