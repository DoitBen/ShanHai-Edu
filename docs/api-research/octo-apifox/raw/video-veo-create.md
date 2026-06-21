# veo创建

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/videos:
    post:
      summary: veo创建
      deprecated: false
      description: >
        # Veo视频生成接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        支持 Veo 模型的文生视频和图生视频，图生视频支持两种模式：

        - **文生视频**：使用 `veo_3_1-fast` 模型

        - **图生视频首尾帧模式**：使用 `veo_3_1-fast-fl` 模型，支持 1～2 张图片作为首尾帧

        - **图生视频参考图模式**：使用 `veo_3_1-fast` 模型，支持最多 3 张参考图片


        ## 请求方式


        支持两种方式，**任选其一**：


        | 方式 | Content-Type | 图生视频时的图片字段 |

        |------|----------------|----------------------|

        | **multipart/form-data** | `multipart/form-data` | 使用
        **`input_reference`**（可重复字段，每张图一个字段），见下文「表单字段说明」 |

        | **application/json** | `application/json` | 必须使用
        **`images`**（字符串数组，**每项对应一张图**）；**每张图的取值类型与表单 `input_reference` 一致**（图片
        URL、Base64 data URI；本地文件见下）。**不得**在 JSON 中使用 `input_reference` /
        `input_reference` |


        说明：除**字段名与结构**不同（表单为重复的 `input_reference`，JSON 为 `images`
        数组）外，**单张图的传法与校验规则与表单相同**。文生视频用 JSON 时不传 `images` 或传空数组 `[]` 即可。


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | `Bearer YOUR_API_KEY` |

        | Content-Type | string | 是 | `multipart/form-data` 或
        `application/json`，须与请求体一致 |


        ## 表单字段说明


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称：文生 `veo_3_1-fast`；首尾帧 `veo_3_1-fast-fl`；参考图
        `veo_3_1-fast` |

        | prompt | string | 是 | 文本提示词 |

        | size | string | 否 | 视频尺寸，格式 `widthxheight`，如
        `1280x720`、`1920x1080`（详见文末说明） |

        | input_reference | 可重复 | 否 |
        图生视频时传递，**同一字段名可重复多次**，每次对应一张图。支持三种取值方式见下表。文生视频不携带本字段即可。 |


        ### `input_reference` 的三种传法


        | 方式 | 说明 |

        |------|------|

        | **本地文件** | multipart 里以文件部件提交，例如 curl 的 `-F
        "input_reference=@/path/to/image.jpg"` |

        | **图片 URL** | 以普通表单文本提交**可公网访问的图片直链**，例如 `-F
        "input_reference=https://example.com/a.png"`（勿传需登录的短链页面） |

        | **Base64** |  以文本字段提交完整 data URI，例如 `-F
        "input_reference=data:image/jpeg;base64,/9j/4AAQSkZJRg..."` 。多图则多个 `-F
        "input_reference=..."`，注意 shell 中转义与长度限制。 |


        JSON 请求中对应写法见下文 **`images` 每项取值**表：每张图一个数组元素，取值规则与上表一致。


        **顺序约定**：

        - **首尾帧模式**：第 1 个 `input_reference` 为首帧，第 2 个为尾帧；仅 1 个时表示只指定首帧。

        - **参考图模式**：最多 3 个 `input_reference`，顺序为参考图 1、2、3。


        ---


        ## JSON 请求体说明（`application/json`）


        ### `images` 每项取值（与表单「单张图」规则一致）


        | 方式 | 表单 `input_reference` | JSON `images` 数组元素 |

        |------|---------------------------|-------------------------|

        | **本地文件** | multipart 中以文件部件上传，例如 `-F
        "input_reference=@/path/to/image.jpg"` | 请求体为纯 JSON
        时无法附带文件部件；请将文件**读成字节后编码为完整 data URI 字符串**写入 `images`，与表单以**文本**提交 Base64
        的方式等价 |

        | **图片 URL** | 表单文本：`-F "input_reference=https://..."` |
        同左：字符串为**可公网访问的图片直链** |

        | **Base64** | 表单文本：`-F "input_reference=data:image/jpeg;base64,..."` |
        同左：字符串为完整 **`data:image/...;base64,...`** |


        多图 = 数组多个元素，**顺序约定与表单相同**（首尾帧：第 1、2 张为首尾；参考图：最多 3 张）。


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 与表单一致：文生 `veo_3_1-fast`；首尾帧 `veo_3_1-fast-fl`；参考图
        `veo_3_1-fast`（若网关另有 slug 以实际为准） |

        | prompt | string | 是 | 文本提示词 |

        | size | string | 否 | 视频尺寸，格式 `widthxheight`，如 `1280x720` |

        | images | string[] | 否 | **图生视频必填**（有图时）：每项为**一张图**，取值见上表（URL / data
        URI 等，规则同表单）。**禁止使用** `input_reference`、`input_reference` 传图。文生视频不传本字段或
        `[]`。 |


        ### JSON 示例 · 图生视频 · 首尾帧（URL 列表）


        ```json

        {
          "model": "veo_3_1-fl",
          "prompt": "广告",
          "size": "1280x720",
          "images": [
            "https://res.papir.cc/user-upload/creati-web-app/2026-04-18/1776519962551vv1AXmBu-ZMWqAckJIbt81167-600x751h.jpg",
            "https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"
          ]
        }

        ```


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d "{\"model\":\"veo_3_1-fl\",\"prompt\":\"广告\",\"size\":\"1280x720\",\"images\":[\"https://example.com/a.png\",\"https://example.com/b.jpg\"]}"
        ```


        ### JSON 示例 · 单张 / 多张 Base64（与表单 data URI 文本一致）


        ```json

        {
          "model": "veo_3_1-fast-fl",
          "prompt": "动画",
          "size": "1280x720",
          "images": [
            "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
          ]
        }

        ```


        ---


        ## 请求示例


        ### 文生视频（仅表单字段，无图片）

        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast" \
          -F "prompt=一只可爱的小猫在花园里玩耍" \
          -F "size=1920x1080"
        ```


        ### 图生视频 · 首尾帧 · 本地文件

        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-fl" \
          -F "prompt=让这两张图之间自然过渡" \
          -F "size=1280x720" \
          -F "input_reference=@/path/to/first_frame.jpg" \
          -F "input_reference=@/path/to/last_frame.jpg"
        ```


        ### 图生视频 · 首尾帧 · 图片 URL（同一字段名重复两次）

        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-fl" \
          -F "prompt=广告" \
          -F "size=1280x720" \
          -F "input_reference=https://example.com/first.png" \
          -F "input_reference=https://example.com/second.jpg"
        ```


        Windows cmd 示例（`curl.exe` 使用 `^` 换行）：

        ```bat

        curl.exe -X POST "https://xxxxx.com/v1/videos" ^
          -H "Authorization: Bearer YOUR_API_KEY" ^
          -F "model=veo_3_1-fast-fl" ^
          -F "prompt=广告" ^
          -F "size=1280x720" ^
          -F "input_reference=https://example.com/img1.png" ^
          -F "input_reference=https://example.com/img2.jpg"
        ```


        ### 图生视频 · 首尾帧 · Base64（文本字段，多图则多个 `input_reference`）

        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-fl" \
          -F "prompt=首尾帧动画" \
          -F "size=1920x1080" \
          -F "input_reference=data:image/jpeg;base64,/9j/4AAQSkZJRg..." \
          -F "input_reference=data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        ```



        ### py示例

        ```

        import requests


        url = "https://xxxx.com/v1/videos"


        headers = {
            "Authorization": "Bearer Bearer YOUR_KEY"
        }


        # multipart/form-data

        files = [
            ("model", (None, "veo_3_1-fast-fl")),
            ("size", (None, "1080x1920")),
            ("prompt", (None, "广告")),

            # 多个 input_reference
            ("input_reference", (None, "https://res.papir.cc/user-upload/creati-web-app/2026-04-18/1776519962551vv1AXmBu-ZMWqAckJIbt81167-600x751h.jpg")),
            ("input_reference", (None, "https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png")),
        ]


        response = requests.post(url, headers=headers, files=files)


        print(response.status_code)

        print(response.text)

        ```


        ### 图生视频 · 参考图 · 本地多文件（最多 3 张）

        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast" \
          -F "prompt=根据参考图生成视频" \
          -F "size=1280x720" \
          -F "input_reference=@/path/to/reference1.jpg" \
          -F "input_reference=@/path/to/reference2.jpg" \
          -F "input_reference=@/path/to/reference3.jpg"
        ```


        ### 图生视频 · 参考图 · URL 或 Base64

        参考图模式同样使用重复的 `input_reference`，每张图为一个 URL 文本或一条 Base64 data
        URI，规则与首尾帧相同，**最多 3 个**。


        ---


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务ID |

        | object | string | 对象类型，固定值：video |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：queued（排队中）、processing（处理中）、completed（已完成）、failed（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅 completed 状态返回） |

        | size | string | 视频尺寸 |


        ## 响应示例


        ### 提交成功（排队中）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "veo_3_1-fast",
          "status": "queued",
          "progress": 0,
          "created_at": 1709876543,
          "size": "1920x1080"
        }

        ```


        ### 任务完成

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "veo_3_1-fast",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876600,
          "size": "1920x1080"
        }

        ```


        ## 查询任务状态


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例

        ```bash

        curl -X GET "https://xxxxx.com/v1/videos/task_xxxxxxxxxxxxx" \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 响应参数

        与提交接口响应参数相同，完成后会包含视频 URL。


        ---


        ## 注意事项


        1. **JSON 与表单二选一**：`application/json` 时图必须用 **`images` 数组**；**不要**在 JSON
        里写 `input_reference`。每张图支持的类型（URL、Base64 data URI、本地文件在 JSON 中以 data URI
        表示）**与表单一致**，仅字段形态不同。


        2. **size 尺寸参数**：
           - 格式为 `widthxheight`，如 `1280x720`、`1920x1080` 等
           - **宽大于高**为横屏（16:9），**高大于宽**为竖屏（9:16）
           - 服务端可能根据尺寸推导分辨率档位后再转发上游，常见规则：
             - 最大边 < 1920 → `720p`
             - 最大边 ≥ 1920 且 < 3840 → `1080p`
           - 推荐：`1280x720`（横屏 720p）、`720x1280`（竖屏 720p）、`1920x1080`（横屏 1080p）、`1080x1920`（竖屏 1080p）

        3. **form-data 下的 input_reference**：
           - 仅适用于 **multipart/form-data**；字段名必须为 **`input_reference`**（含方括号），与多数网关及本客户端约定一致
           - 多图 = 多个同名字段；文件 / URL / Base64 可混用（若网关支持），但需保证顺序符合首尾帧或参考图约定

        4. **模型选择**：
           - **文生视频**：`veo_3_1-fast`；form 不传 `input_reference`；JSON 不传 `images` 或 `images: []`
           - **首尾帧**：`veo_3_1-fast-fl`（部分网关示例为 `veo_3_1-fl`，以实际为准），1～2 张图；form 用 `input_reference`，JSON 用 `images`
           - **参考图**：`veo_3_1-fast`，1～3 张图；form 用 `input_reference`，JSON 用 `images`

        5. **URL / Base64 说明**（表单 `input_reference` 与 JSON `images`
        中的字符串**同样适用**）：URL 须为**图片直链**（返回图片二进制或标准图片 Content-Type），不要传网页 HTML
        地址；需鉴权的链接需带合法 query 或请先下载再以文件上传 / data URI 写入 `images`。Base64 须为完整
        **data URI** 格式，注意体积与网关长度限制。


        6. **异步**：提交成功仅返回任务 id，须轮询 `GET /v1/videos/{task_id}` 获取进度与结果。
      tags:
        - 视频生成（Videos）
      parameters:
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
          required: false
          example: multipart/form-data
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                model:
                  description: 文生视频和参考图模式
                  example: veo_3_1-fast
                  type: string
                prompt:
                  example: 广告
                  type: string
                size:
                  example: 1920x1080
                  type: string
                input_reference:
                  format: binary
                  type: string
                  example: MA==/logo.png
              required:
                - model
                - prompt
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  object:
                    type: string
                  model:
                    type: string
                  status:
                    type: string
                  progress:
                    type: integer
                  created_at:
                    type: integer
                  completed_at:
                    type: integer
                  size:
                    type: string
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - size
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - size
              example:
                id: task_xxxxxxxxxxxxx
                object: video
                model: veo_3_1-fast
                status: completed
                progress: 100
                created_at: 1709876543
                completed_at: 1709876600
                size: 1920x1080
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成（Videos）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-424653897-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
