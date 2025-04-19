# Knowledge Graph System cho Ngành Ngân Hàng

<p align="center">
  <img src="docs/architecture/system_overview.png" alt="Knowledge Graph System Architecture" width="600"/>
</p>

## Giới thiệu

Knowledge Graph System là một hệ thống xây dựng và quản lý đồ thị tri thức bán tự động dành cho lĩnh vực ngân hàng tại Việt Nam. Hệ thống kết hợp các kỹ thuật xử lý ngôn ngữ tự nhiên, machine learning và graph database để tạo ra một cơ sở tri thức toàn diện từ nhiều nguồn dữ liệu khác nhau.

### Tính năng chính

- **Thu thập và xử lý dữ liệu tự động** từ nhiều định dạng (văn bản, HTML, PDF, CSV, JSON)
- **Trích xuất thực thể và mối quan hệ** sử dụng NLP và Machine Learning
- **Tích hợp ontology ngành ngân hàng** để cấu trúc tri thức
- **Giải quyết xung đột dữ liệu** với sự can thiệp của con người
- **API linh hoạt** cho phép tích hợp với các hệ thống khác
- **Giao diện trực quan hóa** đồ thị tri thức
- **Quản lý người dùng và phân quyền** toàn diện

## Kiến trúc hệ thống

Hệ thống được chia thành 5 lớp chính:

1. **Lớp Ứng Dụng**: Giao diện người dùng và tích hợp bên ngoài
2. **Lớp API**: RESTful API cho các ứng dụng client
3. **Lớp Logic Nghiệp Vụ**: Quản lý người dùng, tri thức, nguồn dữ liệu và pipeline
4. **Lớp Xử Lý Dữ Liệu**: Trích xuất, chuyển đổi và làm giàu dữ liệu
5. **Lớp Lưu Trữ Dữ Liệu**: Neo4j, PostgreSQL và AWS S3

## Công nghệ sử dụng

### Backend

- **FastAPI**: Web framework hiệu năng cao

### Frontend

- **React**: SPA framework
- **TailwindCSS**: Utility-first CSS

### Database

- **Neo4j**: Graph database
- **PostgreSQL/Supabase**: Relational database
- **AWS S3**: Lưu trữ đối tượng

### Infrastructure

- **Docker/Docker Compose**: Containerization
- **GitHub Actions**: CI/CD

## Cài đặt

### Yêu cầu

- Docker và Docker Compose
- Python 3.9+
- Node.js 14+

### Sử dụng Docker

```bash
# Clone repository
git clone https://github.com/yourusername/knowledge-graph-system.git
cd knowledge-graph-system

# Tạo file .env từ mẫu
cp .env.example .env
# Chỉnh sửa file .env với thông tin cấu hình của bạn

# Khởi chạy với Docker Compose
docker-compose up -d
```

### Cài đặt thủ công

#### Backend

```bash
# Tạo và kích hoạt môi trường ảo
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Sử dụng

Sau khi cài đặt, bạn có thể truy cập:

- **API Documentation**: http://localhost:8000/docs
- **Admin Console**: http://localhost:3000/admin
- **Consumer UI**: http://localhost:3000

## Data Pipeline

<p align="center">
  <img src="docs/architecture/data_pipeline.png" alt="Data Pipeline" width="600"/>
</p>

Hệ thống xử lý cả dữ liệu có cấu trúc và phi cấu trúc:

1. **Thu thập dữ liệu** từ nhiều nguồn
2. **Trích xuất thực thể và mối quan hệ** bằng NLP
3. **Entity Resolution** để hợp nhất các thực thể trùng lặp
4. **Làm giàu dữ liệu** qua embedding và ontology
5. **Lưu trữ** vào Neo4j và vector database

## Cấu trúc dự án

```
knowledge_graph_system/
├── app/                        # Main application package
│   ├── api/                    # API endpoints
│   ├── core/                   # Core configuration
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── tasks/                  # Background tasks
│   ├── nlp/                    # NLP pipeline
│   └── utils/                  # Utilities
├── data/                       # Data files
├── docs/                       # Documentation
├── frontend/                   # React frontend
├── tests/                      # Test suite
└── docker-compose.yml          # Docker configuration

```

## Đóng góp

Chúng tôi rất hoan nghênh mọi đóng góp! Hãy xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết.

## License

Dự án này được phân phối dưới giấy phép MIT. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## Tài liệu tham khảo

- [Neo4j Documentation](https://neo4j.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
