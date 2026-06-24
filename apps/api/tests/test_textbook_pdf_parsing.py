from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "textbook-parsing" / "renjiao-grade1-volume1-2024"
TEXTBOOK_PDF = FIXTURE_DIR / "1上-人教版小学数学课本（2024新版）.pdf"


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "storage_root": str(tmp_path / "storage"),
            "workflow_root": str(REPO_ROOT / "workflow"),
            "provider_mode": "fake",
        }
    )
    return TestClient(app)


def unwrap(response):
    assert response.status_code < 400, response.text
    payload = response.json()
    assert payload["ok"] is True, payload
    return payload["data"]


def create_project(client: TestClient) -> dict:
    return unwrap(
        client.post(
            "/projects",
            json={
                "name": "PDF教材解析链路测试",
                "subject": "math",
                "grade": "1",
                "textbook_version": "renjiao",
                "volume": "shang",
                "lesson_type": "public",
            },
        )
    )


def upload_fixture_pdf(client: TestClient, project_id: str) -> dict:
    with TEXTBOOK_PDF.open("rb") as textbook:
        return unwrap(
            client.post(
                f"/projects/{project_id}/textbook",
                files={
                    "file": (
                        TEXTBOOK_PDF.name,
                        textbook,
                        "application/pdf",
                    )
                },
            )
        )


def pdf_page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(path)).pages)


def assert_markdown_matches_textbook_contract(markdown: str) -> None:
    required_sections = [
        "## 一、课节范围判断",
        "## 二、核心知识点",
        "## 三、图片、物体、道具清单",
        "## 四、逐页结构化内容",
        "## 五、可转成教案的课堂流程",
        "## 六、可直接形成的教学目标",
        "## 七、建议板书",
        "## 八、输出与核验说明",
    ]
    for section in required_sections:
        assert section in markdown
    assert "待 MinerU 精抽" not in markdown
    assert "当前内容待" not in markdown


def test_fixture_pdf_generates_textbook_outline_and_knowledge_point_markdown(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    uploaded = upload_fixture_pdf(client, project_id)
    assert uploaded["status"] == "uploaded"
    assert uploaded["filename"].endswith(".pdf")

    parse_result = unwrap(
        client.post(
            f"/projects/{project_id}/nodes/textbook_parse/generate",
            json={"knowledge_point_id": "kp_001"},
        )
    )
    content = parse_result["content"]

    assert parse_result["status"] == "needs_review"
    assert content["textbook_meta"] == {
        "subject": "math",
        "grade": "1",
        "textbook_version": "renjiao",
        "volume": "shang",
        "title": "人教版小学数学一年级上册",
    }
    assert content["subject"] == "math"
    assert content["grade"] == "1"
    assert content["textbook_version"] == "renjiao"
    assert content["volume"] == "shang"

    knowledge_points = content["knowledge_points"]
    assert len(knowledge_points) >= 9
    assert [point["title"] for point in knowledge_points[:9]] == [
        "5以内数的认识",
        "1-5的加、减法",
        "0的认识和加、减法",
        "整理和复习（5以内数）",
        "6-10的认识",
        "6-9的加、减法",
        "10的认识和加、减法",
        "连加、连减",
        "整理和复习（6-10）",
    ]
    assert any(point["title"] == "5以内数的认识" for point in knowledge_points)
    selected = content["selected_knowledge_point"]
    assert selected["knowledge_point_id"] == "kp_001"
    assert selected["title"] == "5以内数的认识"
    assert "5以内数的认识" in selected["markdown"]
    assert selected["markdown_path"].endswith("knowledge-points/kp_001.md")
    assert Path(project["project_dir"], selected["markdown_path"]).exists()
    asset_package = selected["asset_package"]
    assert asset_package["source_pdf_path"].endswith(".pdf")
    assert asset_package["slice_pdf_path"].endswith("knowledge-points/kp_001/source.pdf")
    assert asset_package["mineru_md_path"].endswith("knowledge-points/kp_001/mineru.md")
    assert asset_package["textbook_pages"] == "14-23"
    assert asset_package["pdf_pages"] == "19-28"
    assert asset_package["parse_status"] == "parsed"
    assert asset_package["review_status"] == "needs_review"
    assert Path(project["project_dir"], asset_package["slice_pdf_path"]).exists()
    assert Path(project["project_dir"], asset_package["mineru_md_path"]).exists()

    source_pdf = Path(project["project_dir"], asset_package["source_pdf_path"])
    slice_pdf = Path(project["project_dir"], asset_package["slice_pdf_path"])
    assert pdf_page_count(slice_pdf) == 10
    assert pdf_page_count(slice_pdf) < pdf_page_count(source_pdf)

    markdown = Path(project["project_dir"], asset_package["mineru_md_path"]).read_text(encoding="utf-8")
    assert_markdown_matches_textbook_contract(markdown)


def test_textbook_library_lists_seed_fixture_and_lesson_assets(tmp_path: Path):
    client = make_client(tmp_path)

    library = unwrap(client.get("/textbook-library"))
    assert library["textbooks"], library
    fixture = library["textbooks"][0]
    assert fixture["textbook_id"] == "renjiao-grade1-volume1-2024"
    assert fixture["title"] == "人教版小学数学一年级上册"
    assert fixture["publisher"] == "人教版"
    assert fixture["subject_label"] == "小学数学"
    assert fixture["grade_label"] == "一年级"
    assert fixture["volume_label"] == "上册"
    assert fixture["display_name"] == "人教版 / 小学数学 / 一年级 / 上册"
    assert fixture["status"] == "indexed"

    lessons = unwrap(client.get(f"/textbook-library/{fixture['textbook_id']}/knowledge-points"))
    assert [chapter["title"] for chapter in lessons["chapters"]] == [
        "数学游戏",
        "5以内数的认识和加、减法",
        "6~10的认识和加、减法",
        "认识立体图形",
        "11~20的认识",
        "20以内的进位加法",
        "复习与关联",
    ]
    assert lessons["chapters"][0] == {
        "chapter_id": "ch_001",
        "title": "数学游戏",
        "page_start": 1,
        "page_end": 11,
        "pdf_page_start": 6,
        "pdf_page_end": 16,
        "source": "toc",
        "review_status": "needs_review",
    }
    assert lessons["chapters"][1]["page_start"] == 12
    assert lessons["chapters"][1]["page_end"] == 33
    assert lessons["chapters"][1]["pdf_page_start"] == 17
    assert lessons["chapters"][1]["pdf_page_end"] == 38
    assert len(lessons["knowledge_points"]) >= 9
    first_point = lessons["knowledge_points"][0]
    assert first_point["title"] == "5以内数的认识"
    assert first_point["chapter_id"] == "ch_002"
    assert first_point["unit"] == "5以内数的认识和加、减法"
    assert first_point["page_start"] == 14
    assert first_point["page_end"] == 23
    assert first_point["pdf_page_start"] == 19
    assert first_point["pdf_page_end"] == 28
    assert first_point["keywords"] == ["1-5", "比大小", "第几", "分与合"]
    assert first_point["parse_status"] == "parsed"
    assert first_point["review_status"] == "needs_review"
    assert all(point.get("chapter_id") for point in lessons["knowledge_points"])
    assert all(point["title"] not in {chapter["title"] for chapter in lessons["chapters"]} for point in lessons["knowledge_points"])

    asset = unwrap(client.get(f"/textbook-library/{fixture['textbook_id']}/knowledge-points/kp_001/assets"))
    assert asset["knowledge_point_id"] == "kp_001"
    assert asset["chapter_id"] == "ch_002"
    assert asset["slice_pdf_path"].endswith("knowledge-points/kp_001/source.pdf")
    assert asset["mineru_md_path"].endswith("knowledge-points/kp_001/mineru.md")


def test_textbook_library_unknown_knowledge_point_returns_stable_error(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.get("/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_missing/assets")
    payload = response.json()

    assert response.status_code == 404
    assert payload["ok"] is False
    assert payload["error"]["code"] == "TEXTBOOK_ASSET_NOT_FOUND"
    assert "Unknown knowledge point: kp_missing" in payload["error"]["message"]


def test_textbook_library_uploads_fixture_into_global_db_and_tracks_job(tmp_path: Path):
    client = make_client(tmp_path)

    with TEXTBOOK_PDF.open("rb") as textbook:
        uploaded = unwrap(
            client.post(
                "/textbook-library/uploads",
                files={"file": (TEXTBOOK_PDF.name, textbook, "application/pdf")},
            )
        )

    assert uploaded["textbook_id"] == "renjiao-grade1-volume1-2024"
    assert uploaded["textbook_version_id"] == "renjiao-grade1-volume1-2024-v1"
    assert uploaded["job_id"]
    assert uploaded["parse_status"] == "uploaded"

    job = unwrap(client.get(f"/textbook-library/jobs/{uploaded['job_id']}"))
    assert job["job_id"] == uploaded["job_id"]
    assert job["status"] in {"indexed", "approved"}
    assert job["textbook_id"] == uploaded["textbook_id"]

    asset = unwrap(client.get(f"/textbook-library/{uploaded['textbook_id']}/knowledge-points/kp_001/assets"))
    assert asset["parse_status"] in {"indexed", "parsed"}
    assert asset["review_status"] == "needs_review"
    assert not Path(asset["slice_pdf_path"]).exists()
    assert not Path(asset["mineru_md_path"]).exists()

    library = unwrap(client.get("/textbook-library"))
    fixture = next(item for item in library["textbooks"] if item["textbook_id"] == uploaded["textbook_id"])
    assert fixture["knowledge_point_count"] >= 9
    assert Path(tmp_path, "storage", "textbook_library.db").exists()


def test_textbook_library_can_split_selected_assets_without_mineru_markdown(tmp_path: Path):
    client = make_client(tmp_path)

    split = unwrap(
        client.post(
            "/textbook-library/renjiao-grade1-volume1-2024/split",
            json={"knowledge_point_ids": ["kp_001", "kp_006"]},
        )
    )

    assert split["job_type"] == "textbook_split"
    assert split["status"] == "split_ready"
    assert split["requested_count"] == 2
    assert split["successful_count"] == 2
    assert {item["knowledge_point_id"] for item in split["assets"]} == {"kp_001", "kp_006"}
    for item in split["assets"]:
        assert item["parse_status"] == "split_ready"
        assert item["review_status"] == "unreviewed"
        assert Path(item["slice_pdf_path"]).exists()
        assert not Path(item["mineru_md_path"]).exists()

    asset = unwrap(client.get("/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_006/assets"))
    assert asset["parse_status"] == "split_ready"
    assert asset["review_status"] == "unreviewed"
    assert Path(asset["slice_pdf_path"]).exists()
    assert not Path(asset["mineru_md_path"]).exists()


def test_textbook_library_can_extract_selected_assets_after_split(tmp_path: Path):
    client = make_client(tmp_path)

    unwrap(
        client.post(
            "/textbook-library/renjiao-grade1-volume1-2024/split",
            json={"knowledge_point_ids": ["kp_006"]},
        )
    )
    extracted = unwrap(
        client.post(
            "/textbook-library/renjiao-grade1-volume1-2024/assets/extract",
            json={"knowledge_point_ids": ["kp_006"]},
        )
    )

    assert extracted["job_type"] == "mineru_extract_batch"
    assert extracted["status"] == "needs_review"
    assert extracted["requested_count"] == 1
    assert extracted["successful_count"] == 1
    assert extracted["failed_count"] == 0
    asset = extracted["assets"][0]
    assert asset["knowledge_point_id"] == "kp_006"
    assert asset["parse_status"] == "needs_review"
    assert asset["review_status"] == "needs_review"
    assert Path(asset["slice_pdf_path"]).exists()
    assert Path(asset["mineru_md_path"]).exists()


def test_textbook_library_can_split_and_extract_all_assets_without_project_id(tmp_path: Path):
    client = make_client(tmp_path)

    split = unwrap(client.post("/textbook-library/renjiao-grade1-volume1-2024/split", json={}))
    assert split["job_type"] == "textbook_split"
    assert split["status"] == "split_ready"
    assert split["requested_count"] >= 9
    assert split["successful_count"] == split["requested_count"]
    assert all(item["textbook_id"] == "renjiao-grade1-volume1-2024" for item in split["assets"])
    assert all("project_id" not in item for item in split["assets"])

    extracted = unwrap(client.post("/textbook-library/renjiao-grade1-volume1-2024/assets/extract", json={}))
    assert extracted["job_type"] == "mineru_extract_batch"
    assert extracted["status"] == "needs_review"
    assert extracted["requested_count"] == split["requested_count"]
    assert extracted["successful_count"] == extracted["requested_count"]
    assert all(item["parse_status"] == "needs_review" for item in extracted["assets"])
    assert all(item["review_status"] == "needs_review" for item in extracted["assets"])


def test_textbook_library_batch_rejects_invalid_knowledge_point_ids_with_stable_error(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post(
        "/textbook-library/renjiao-grade1-volume1-2024/split",
        json={"knowledge_point_ids": ["kp_001", "kp_missing"]},
    )
    payload = response.json()

    assert response.status_code == 404
    assert payload["ok"] is False
    assert payload["error"]["code"] == "TEXTBOOK_ASSET_NOT_FOUND"
    assert "kp_missing" in payload["error"]["message"]


def test_textbook_library_asset_extract_and_confirm_updates_review_status(tmp_path: Path):
    client = make_client(tmp_path)

    extracted = unwrap(
        client.post(
            "/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_006/assets/extract",
            json={},
        )
    )

    assert extracted["asset_id"]
    assert extracted["mineru_job_id"]
    assert extracted["knowledge_point_id"] == "kp_006"
    assert extracted["slice_pdf_path"].endswith("knowledge-points/kp_006/source.pdf")
    assert extracted["mineru_md_path"].endswith("knowledge-points/kp_006/mineru.md")
    assert extracted["parse_status"] in {"indexed", "parsed", "needs_review"}
    assert extracted["review_status"] == "needs_review"

    confirmed = unwrap(
        client.post(
            f"/textbook-library/assets/{extracted['asset_id']}/confirm",
            json={"reviewer": "qa"},
        )
    )

    assert confirmed["asset_id"] == extracted["asset_id"]
    assert confirmed["review_status"] == "approved"
    assert confirmed["parse_status"] == "approved"


def test_textbook_library_extract_writes_real_slice_and_contract_markdown(tmp_path: Path):
    client = make_client(tmp_path)

    extracted = unwrap(
        client.post(
            "/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_006/assets/extract",
            json={},
        )
    )

    slice_pdf = Path(extracted["slice_pdf_path"])
    source_pdf = Path(extracted["source_pdf_path"])
    assert slice_pdf.exists()
    assert source_pdf.exists()
    assert pdf_page_count(slice_pdf) == 10
    assert pdf_page_count(slice_pdf) < pdf_page_count(source_pdf)

    markdown = Path(extracted["mineru_md_path"]).read_text(encoding="utf-8")
    assert "6-9的加、减法" in markdown
    assert_markdown_matches_textbook_contract(markdown)
    assert extracted["checksum"].startswith("sha256:")


def test_textbook_library_extract_failure_does_not_copy_full_pdf_or_allow_confirm(tmp_path: Path, monkeypatch):
    client = make_client(tmp_path)

    def fail_slice(*_args, **_kwargs):
        raise RuntimeError("slice failed for regression")

    monkeypatch.setattr("app.textbook_parser.TextbookParser._write_pdf_slice", fail_slice)

    response = client.post(
        "/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_006/assets/extract",
        json={},
    )
    payload = response.json()

    assert response.status_code == 409
    assert payload["ok"] is False
    assert payload["error"]["code"] == "TEXTBOOK_ASSET_EXTRACT_FAILED"
    details = payload["error"]["details"]
    assert details["parse_status"] == "failed"
    assert details["review_status"] == "needs_review"
    assert "slice failed for regression" in details["diagnostics"]["message"]

    asset = unwrap(client.get("/textbook-library/renjiao-grade1-volume1-2024/knowledge-points/kp_006/assets"))
    assert asset["parse_status"] == "failed"
    assert asset["review_status"] == "needs_review"
    assert asset["diagnostics"]["stage"] == "pdf_slice"
    assert not Path(asset["slice_pdf_path"]).exists()

    confirm_response = client.post(f"/textbook-library/assets/{asset['asset_id']}/confirm", json={"reviewer": "qa"})
    confirm_payload = confirm_response.json()
    assert confirm_response.status_code == 409
    assert confirm_payload["ok"] is False
    assert confirm_payload["error"]["code"] == "TEXTBOOK_ASSET_NOT_TRUSTED"


def test_fixture_pdf_can_switch_selected_lesson_knowledge_point(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    parse_result = unwrap(
        client.post(
            f"/projects/{project_id}/nodes/textbook_parse/generate",
            json={"knowledge_point_id": "kp_006"},
        )
    )
    content = parse_result["content"]
    selected = content["selected_knowledge_point"]

    assert selected["knowledge_point_id"] == "kp_006"
    assert selected["title"] == "6-9的加、减法"
    assert selected["source_pages"] == {
        "textbook_pages": "44-53",
        "pdf_pages": "49-58",
    }
    assert selected["markdown_path"].endswith("knowledge-points/kp_006.md")
    assert "6-9的加、减法" in selected["markdown"]
    assert_markdown_matches_textbook_contract(selected["markdown"])
    assert Path(project["project_dir"], selected["markdown_path"]).exists()
    slice_pdf = Path(project["project_dir"], selected["asset_package"]["slice_pdf_path"])
    assert pdf_page_count(slice_pdf) == 10
    assert pdf_page_count(slice_pdf) < pdf_page_count(Path(project["project_dir"], selected["asset_package"]["source_pdf_path"]))


def test_fixture_pdf_rejects_unknown_knowledge_point(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    response = client.post(
        f"/projects/{project_id}/nodes/textbook_parse/generate",
        json={"knowledge_point_id": "kp_missing"},
    )
    payload = response.json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] == "GENERATION_INPUT_INVALID"
    assert "Unknown knowledge point: kp_missing" in payload["error"]["message"]


def test_project_metadata_can_be_updated_after_textbook_parse_prefill(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]

    updated = unwrap(
        client.patch(
            f"/projects/{project_id}",
            json={
                "name": "教师手改项目名",
                "subject": "math",
                "grade": "2",
                "textbook_version": "renjiao",
                "volume": "xia",
                "lesson_type": "review",
                "textbook_id": "renjiao-grade1-volume1-2024",
                "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
                "knowledge_point_id": "kp_006",
            },
        )
    )

    assert updated["project_id"] == project_id
    assert updated["name"] == "教师手改项目名"
    assert updated["grade"] == "2"
    assert updated["volume"] == "xia"
    assert updated["lesson_type"] == "review"
    assert updated["textbook_id"] == "renjiao-grade1-volume1-2024"
    assert updated["textbook_version_id"] == "renjiao-grade1-volume1-2024-v1"
    assert updated["knowledge_point_id"] == "kp_006"


def test_lesson_plan_uses_selected_knowledge_point_markdown(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    lesson = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))
    content = lesson["content"]

    assert lesson["status"] == "needs_review"
    assert content["source_knowledge_point_id"] == "kp_001"
    assert content["source_markdown_path"].endswith("knowledge-points/kp_001.md")
    assert content["source_textbook_id"] == "renjiao-grade1-volume1-2024"
    assert content["source_slice_pdf_path"].endswith("knowledge-points/kp_001/source.pdf")
    assert content["source_mineru_md_path"].endswith("knowledge-points/kp_001/mineru.md")
    assert "5以内数的认识" in content["lesson_plan_markdown"]
    assert "5以内数的认识" in content["textbook_anchor"]


def test_lesson_plan_uses_switched_knowledge_point_markdown(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    unwrap(
        client.post(
            f"/projects/{project_id}/nodes/textbook_parse/generate",
            json={"knowledge_point_id": "kp_006"},
        )
    )
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))

    lesson = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))
    content = lesson["content"]

    assert lesson["status"] == "needs_review"
    assert content["source_knowledge_point_id"] == "kp_006"
    assert content["source_markdown_path"].endswith("knowledge-points/kp_006.md")
    assert "6-9的加、减法" in content["lesson_plan_markdown"]
    assert "6-9的加、减法" in content["textbook_anchor"]


def test_lesson_plan_library_import_and_reference_id_are_persisted_without_replacing_textbook_source(tmp_path: Path):
    client = make_client(tmp_path)
    project = create_project(client)
    project_id = project["project_id"]
    upload_fixture_pdf(client, project_id)

    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/generate", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/textbook_parse/approve", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/generate", json={}))
    unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/approve", json={}))

    imported = unwrap(
        client.post(
            "/lesson-plan-library/import/from-project",
            json={"project_id": project_id, "created_by": "qa"},
        )
    )
    assert imported["lesson_plan_id"]
    assert imported["source_project_id"] == project_id
    assert imported["source_textbook_id"] == "renjiao-grade1-volume1-2024"
    assert imported["source_knowledge_point_id"] == "kp_001"

    references = unwrap(
        client.get(
            "/lesson-plan-library",
            params={
                "textbook_id": "renjiao-grade1-volume1-2024",
                "knowledge_point_id": "kp_001",
            },
        )
    )
    assert any(item["lesson_plan_id"] == imported["lesson_plan_id"] for item in references["lesson_plans"])

    updated = unwrap(
        client.patch(
            f"/projects/{project_id}",
            json={"reference_lesson_plan_id": imported["lesson_plan_id"]},
        )
    )
    assert updated["reference_lesson_plan_id"] == imported["lesson_plan_id"]

    regenerated = unwrap(client.post(f"/projects/{project_id}/nodes/lesson_plan/retry"))
    content = regenerated["content"]
    assert content["reference_lesson_plan_id"] == imported["lesson_plan_id"]
    assert content["reference_lesson_plan"]["lesson_plan_id"] == imported["lesson_plan_id"]
    assert content["source_knowledge_point_id"] == "kp_001"
    assert content["source_mineru_md_path"].endswith("knowledge-points/kp_001/mineru.md")


def test_lesson_plan_library_uploads_markdown_and_returns_teacher_readable_metadata(tmp_path: Path):
    client = make_client(tmp_path)

    markdown = "# 6-9的加、减法公开课教案\n\n## 教学目标\n学生能结合情境理解加减法。"
    uploaded = unwrap(
        client.post(
            "/lesson-plan-library/uploads",
            data={
                "textbook_id": "renjiao-grade1-volume1-2024",
                "textbook_version_id": "renjiao-grade1-volume1-2024-v1",
                "knowledge_point_id": "kp_006",
                "created_by": "admin",
            },
            files={"file": ("6-9-add-subtract.md", markdown.encode("utf-8"), "text/markdown")},
        )
    )

    assert uploaded["lesson_plan_id"]
    assert uploaded["title"] == "6-9的加、减法公开课教案"
    assert uploaded["source_project_id"] is None
    assert uploaded["source_textbook_id"] == "renjiao-grade1-volume1-2024"
    assert uploaded["source_knowledge_point_id"] == "kp_006"
    assert uploaded["metadata"]["source_label"] == "管理员上传"
    assert uploaded["metadata"]["textbook_display_name"] == "人教版 / 小学数学 / 一年级 / 上册"
    assert uploaded["metadata"]["knowledge_point_title"] == "6-9的加、减法"
    assert uploaded["metadata"]["created_by_label"] == "admin"
    assert uploaded["metadata"]["markdown_excerpt"].startswith("# 6-9的加、减法公开课教案")

    listed = unwrap(
        client.get(
            "/lesson-plan-library",
            params={
                "textbook_id": "renjiao-grade1-volume1-2024",
                "knowledge_point_id": "kp_006",
            },
        )
    )
    summary = next(item for item in listed["lesson_plans"] if item["lesson_plan_id"] == uploaded["lesson_plan_id"])
    assert summary["metadata"]["source_label"] == "管理员上传"
    assert summary["metadata"]["knowledge_point_title"] == "6-9的加、减法"
    assert summary["metadata"]["textbook_display_name"] == "人教版 / 小学数学 / 一年级 / 上册"


def test_lesson_plan_library_upload_rejects_missing_markdown_with_stable_error(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.post(
        "/lesson-plan-library/uploads",
        data={
            "textbook_id": "renjiao-grade1-volume1-2024",
            "knowledge_point_id": "kp_001",
        },
        files={"file": ("empty.md", b"   \n", "text/markdown")},
    )
    payload = response.json()

    assert response.status_code == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] == "LESSON_PLAN_UPLOAD_INVALID"
