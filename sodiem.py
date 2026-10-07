from flask import (
    Flask,
    request,
    redirect,
    url_for,
    abort,
    jsonify,
    make_response,
)
from markupsafe import escape

from sinhvien import STUDENTS


app = Flask(__name__)

app.json.ensure_ascii = False


# =========================================================
# HELPERS
# =========================================================

def average(scores):
    if not scores:
        return None

    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    if avg is None:
        return "Chưa có điểm"

    if avg >= 8.5:
        return "Giỏi"

    if avg >= 7.0:
        return "Khá"

    if avg >= 5.0:
        return "Trung bình"

    return "Yếu"


def student_summary(mssv):
    student = STUDENTS[mssv]

    avg = average(student["scores"])

    return {
        "mssv": mssv,
        "name": student["name"],
        "lop": student["lop"],
        "scores": student["scores"],
        "average": avg,
        "rank": rank(avg),
    }


def layout(title, body):
    return f"""
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>{escape(title)} - Sổ điểm</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
        }}

        nav {{
            margin-bottom: 30px;
        }}

        nav a {{
            margin-right: 15px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
        }}

        th,
        td {{
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }}

        th {{
            background: #f2f2f2;
        }}

        form {{
            margin: 15px 0;
        }}

        input,
        button {{
            padding: 7px;
        }}

        .filter {{
            margin-bottom: 20px;
        }}
    </style>
</head>

<body>

<nav>
    <a href="{url_for('home')}">
        Trang chủ
    </a>

    <a href="{url_for('student_list')}">
        Sinh viên
    </a>

    <a href="{url_for('search')}">
        Tìm kiếm
    </a>
</nav>

{body}

</body>
</html>
"""


# =========================================================
# C1 - TRANG CHỦ
# =========================================================

@app.route("/")
def home():
    total_students = len(STUDENTS)

    classes = {
        student["lop"]
        for student in STUDENTS.values()
    }

    total_classes = len(classes)

    body = f"""
    <h1>Sổ điểm lớp học</h1>

    <p>
        Tổng số sinh viên:
        <strong>{total_students}</strong>
    </p>

    <p>
        Số lớp:
        <strong>{total_classes}</strong>
    </p>

    <p>
        <a href="{url_for('student_list')}">
            Xem danh sách sinh viên
        </a>
    </p>

    <p>
        <a href="{url_for('api_students')}">
            API sinh viên
        </a>
    </p>
    """

    return layout(
        "Trang chủ",
        body
    )


# =========================================================
# C2 - DANH SÁCH SINH VIÊN
# =========================================================

@app.route("/students")
def student_list():
    lop = request.args.get("lop", "")

    students = []

    for mssv in STUDENTS:
        summary = student_summary(mssv)

        if (
            lop
            and summary["lop"].lower()
            != lop.lower()
        ):
            continue

        students.append(summary)

    classes = sorted({
        student["lop"]
        for student in STUDENTS.values()
    })

    filter_links = """
    <div class="filter">
        <strong>Lọc lớp:</strong>
    """

    filter_links += f"""
        <a href="{url_for('student_list')}">
            Tất cả
        </a>
    """

    for class_name in classes:
        filter_links += f"""
        <a href="{url_for(
            'student_list',
            lop=class_name
        )}">
            {escape(class_name)}
        </a>
        """

    filter_links += """
    </div>
    """

    if not students:
        body = f"""
        <h1>Danh sách sinh viên</h1>

        {filter_links}

        <p>
            Không có sinh viên phù hợp.
        </p>
        """

        return layout(
            "Danh sách sinh viên",
            body
        )

    rows = ""

    for student in students:
        if student["average"] is None:
            average_display = "—"
        else:
            average_display = str(
                student["average"]
            )

        rows += f"""
        <tr>
            <td>
                <a href="{url_for(
                    'student_detail',
                    mssv=student['mssv']
                )}">
                    {escape(student["mssv"])}
                </a>
            </td>

            <td>
                {escape(student["name"])}
            </td>

            <td>
                {escape(student["lop"])}
            </td>

            <td>
                {escape(average_display)}
            </td>

            <td>
                {escape(student["rank"])}
            </td>
        </tr>
        """

    body = f"""
    <h1>Danh sách sinh viên</h1>

    {filter_links}

    <table>
        <thead>
            <tr>
                <th>MSSV</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                <th>Điểm TB</th>
                <th>Xếp loại</th>
            </tr>
        </thead>

        <tbody>
            {rows}
        </tbody>
    </table>
    """

    return layout(
        "Danh sách sinh viên",
        body
    )


# =========================================================
# C3 - CHI TIẾT SINH VIÊN
# =========================================================

@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(
            404,
            description=(
                f"Không có sinh viên với MSSV = {mssv}."
            )
        )

    student = student_summary(mssv)

    if student["average"] is None:
        average_display = "—"
    else:
        average_display = str(
            student["average"]
        )

    rows = ""

    for course, score in student["scores"].items():
        rows += f"""
        <tr>
            <td>
                {escape(course)}
            </td>

            <td>
                {escape(str(score))}
            </td>
        </tr>
        """

    body = f"""
    <h1>Thông tin sinh viên</h1>

    <p>
        <strong>Họ tên:</strong>
        {escape(student["name"])}
    </p>

    <p>
        <strong>MSSV:</strong>
        {escape(student["mssv"])}
    </p>

    <p>
        <strong>Lớp:</strong>

        <a href="{url_for(
            'student_list',
            lop=student['lop']
        )}">
            {escape(student["lop"])}
        </a>
    </p>

    <p>
        <strong>Điểm TB:</strong>
        {escape(average_display)}
    </p>

    <p>
        <strong>Xếp loại:</strong>
        {escape(student["rank"])}
    </p>

    <h2>Bảng điểm</h2>

    <table>
        <thead>
            <tr>
                <th>Học phần</th>
                <th>Điểm</th>
            </tr>
        </thead>

        <tbody>
            {rows}
        </tbody>
    </table>

    <p>
        <a href="{url_for(
            'export_scores',
            mssv=mssv
        )}">
            Tải bảng điểm (CSV)
        </a>
    </p>

    <p>
        Link rút gọn:

        <a href="{url_for(
            'short_student',
            mssv=mssv
        )}">
            {escape(
                url_for(
                    'short_student',
                    mssv=mssv
                )
            )}
        </a>
    </p>
    """

    return layout(
        f"Chi tiết {student['name']}",
        body
    )


# =========================================================
# C4 - REDIRECT 301
# =========================================================

@app.route("/sv/<mssv>")
def short_student(mssv):
    return redirect(
        url_for(
            "student_detail",
            mssv=mssv
        ),
        code=301
    )


# =========================================================
# Q5 - EXPORT CSV
# =========================================================

@app.route("/students/<mssv>/export")
def export_scores(mssv):
    if mssv not in STUDENTS:
        abort(
            404,
            description=(
                f"Không có sinh viên với MSSV = {mssv}."
            )
        )

    student = STUDENTS[mssv]

    lines = [
        "hoc_phan,diem"
    ]

    for course, score in student["scores"].items():
        lines.append(
            f"{course},{score}"
        )

    csv_content = "\n".join(lines)

    response = make_response(
        csv_content
    )

    response.headers["Content-Type"] = (
        "text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        f"attachment; filename=diem_{mssv}.csv"
    )

    return response


# =========================================================
# C6 - TÌM KIẾM
# =========================================================

@app.route("/search")
def search():
    keyword = request.args.get("q", "")

    keyword_lower = keyword.lower()

    results = []

    for mssv, student in STUDENTS.items():

        if (
            keyword_lower in student["name"].lower()
            or keyword_lower in mssv.lower()
        ):
            results.append(
                student_summary(mssv)
            )

    rows = ""

    for student in results:
        rows += f"""
        <li>
            <a href="{url_for(
                'student_detail',
                mssv=student['mssv']
            )}">
                {escape(student["name"])}
                ({escape(student["mssv"])})
            </a>
        </li>
        """

    body = f"""
    <h1>Tìm kiếm sinh viên</h1>

    <form
        method="get"
        action="{url_for('search')}"
    >

        <input
            type="text"
            name="q"
            value="{escape(keyword)}"
            placeholder="Nhập họ tên hoặc MSSV"
        >

        <button type="submit">
            Tìm kiếm
        </button>

    </form>

    <p>
        Tìm thấy {len(results)} kết quả
        cho “{escape(keyword)}”
    </p>

    <ul>
        {rows}
    </ul>
    """

    return layout(
        "Tìm kiếm",
        body
    )


# =========================================================
# C7 - API DANH SÁCH
# =========================================================

@app.route("/api/students")
def api_students():
    lop = request.args.get("lop")

    min_avg_raw = request.args.get("min_avg")

    # Không truyền min_avg
    if min_avg_raw is None:
        min_avg = None

    # Có truyền nhưng sai kiểu
    else:
        try:
            min_avg = float(min_avg_raw)

        except ValueError:
            abort(
                400,
                description="min_avg phải là một số."
            )

    students = []

    for mssv in STUDENTS:
        summary = student_summary(mssv)

        # Lọc theo lớp
        if lop:
            if summary["lop"].lower() != lop.lower():
                continue

        # Lọc theo điểm trung bình
        if min_avg is not None:

            # Không có điểm thì bỏ qua
            if summary["average"] is None:
                continue

            if summary["average"] < min_avg:
                continue

        students.append(summary)

    return jsonify(students)


# =========================================================
# C7 - API CHI TIẾT
# =========================================================

@app.route("/api/students/<mssv>")
def api_student_detail(mssv):
    if mssv not in STUDENTS:
        abort(
            404,
            description=(
                f"Không có sinh viên với MSSV = {mssv}."
            )
        )

    return jsonify(
        student_summary(mssv)
    )


# =========================================================
# C8 - API ĐIỂM
# =========================================================

@app.route(
    "/api/students/<mssv>/scores/<course>",
    methods=[
        "GET",
        "PUT",
        "DELETE",
    ],
)
def api_score(mssv, course):

    # Kiểm tra MSSV
    if mssv not in STUDENTS:
        abort(
            404,
            description=(
                f"Không có sinh viên với MSSV = {mssv}."
            )
        )

    student = STUDENTS[mssv]

    # Course không phân biệt hoa thường
    course = course.upper()

    scores = student["scores"]

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    if request.method == "GET":

        if course not in scores:
            abort(
                404,
                description=(
                    f"Sinh viên chưa có điểm "
                    f"học phần {course}."
                )
            )

        return jsonify({
            "mssv": mssv,
            "course": course,
            "score": scores[course],
        })

    # -----------------------------------------------------
    # PUT
    # -----------------------------------------------------

    if request.method == "PUT":

        score_raw = request.args.get("score")

        # Không có score
        if score_raw is None:
            abort(
                400,
                description="Thiếu tham số score."
            )

        # score không phải số
        try:
            score = float(score_raw)

        except ValueError:
            abort(
                400,
                description="score phải là một số."
            )

        # score ngoài khoảng
        if score < 0 or score > 10:
            abort(
                400,
                description=(
                    "score phải nằm trong khoảng "
                    "từ 0 đến 10."
                )
            )

        # Kiểm tra môn đã tồn tại chưa
        is_new = course not in scores

        # Lưu điểm
        scores[course] = score

        # Tính lại điểm trung bình
        avg = average(scores)

        response_data = {
            "mssv": mssv,
            "course": course,
            "score": score,
            "average": avg,
        }

        # Thêm môn mới → 201
        if is_new:

            response = make_response(
                jsonify(response_data),
                201
            )

            response.headers["Location"] = url_for(
                "api_score",
                mssv=mssv,
                course=course
            )

            return response

        # Sửa môn cũ → 200
        return jsonify(response_data)

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    if request.method == "DELETE":

        if course not in scores:
            abort(
                404,
                description=(
                    f"Sinh viên chưa có điểm "
                    f"học phần {course}."
                )
            )

        del scores[course]

        return "", 204


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    if request.path.startswith("/api/"):
        response = jsonify({
            "error": error.name,
            "detail": error.description,
        })

        response.status_code = error.code

        return response

    body = f"""
    <h1>{error.code}</h1>

    <h2>{escape(error.name)}</h2>

    <p>{escape(error.description)}</p>

    <p>
        <a href="{url_for('home')}">
            Về trang chủ
        </a>
    </p>
    """

    response = make_response(
        layout(error.name, body),
        error.code
    )

    return response
if __name__ == "__main__":
    app.run(debug=True)
