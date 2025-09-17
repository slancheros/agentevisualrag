# ===========================
# Makefile - Visual Agent RAG
# ===========================

# ---- Variables (puedes overridear en la invocación: make index WVT_CLASS=MyClass) ----
WEAVIATE_URL ?= http://localhost:8080
API_URL      ?= http://localhost:8000
WVT_CLASS    ?= FashionItem
TOP_K        ?= 8
QUERY_IMAGE  ?= data/images/SYNTH/img_0001.jpg

# ---- Helpers ----
CURL ?= curl -s
COMPOSE ?= docker compose

# ---- Ayuda ----
.PHONY: help
help:
	@echo "Comandos disponibles:"
	@echo "  make up           - Levanta Weaviate + API"
	@echo "  make up-all       - Levanta Weaviate + API + (no indexa) "
	@echo "  make down         - Baja todos los servicios"
	@echo "  make logs-app     - Logs del servicio app"
	@echo "  make logs-weav    - Logs de Weaviate"
	@echo "  make index        - Ejecuta el indexer (one-shot), sube objetos a Weaviate"
	@echo "  make reindex      - Borra la clase $(WVT_CLASS) y vuelve a indexar"
	@echo "  make check        - Revisa READY, schema, totalResults y muestra 3 items"
	@echo "  make retrieve     - Llama /retrieve con QUERY_IMAGE=$(QUERY_IMAGE), TOP_K=$(TOP_K)"
	@echo "  make clean-docker - Limpia cache y recursos no usados de Docker"
	@echo ""
	@echo "Variables configurables: WEAVIATE_URL=$(WEAVIATE_URL)  API_URL=$(API_URL)  WVT_CLASS=$(WVT_CLASS)"
	@echo "                         QUERY_IMAGE=$(QUERY_IMAGE)  TOP_K=$(TOP_K)"

# ---- Orquestación ----
.PHONY: up
up:
	$(COMPOSE) up -d weaviate app

.PHONY: up-all
up-all:
	$(COMPOSE) up -d

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: logs-app
logs-app:
	$(COMPOSE) logs -f app

.PHONY: logs-weav
logs-weav:
	$(COMPOSE) logs -f weaviate

# ---- Indexado ----
.PHONY: index
index:
	$(COMPOSE) run --rm indexer

.PHONY: reindex
reindex:
	@echo "Borrando clase $(WVT_CLASS) (si existe)..."
	-$(CURL) -X DELETE "$(WEAVIATE_URL)/v1/schema/$(WVT_CLASS)" >/dev/null || true
	$(MAKE) index

# ---- Chequeos ----
.PHONY: check
check:
	WEAVIATE_URL=$(WEAVIATE_URL) WVT_CLASS=$(WVT_CLASS) python check_weaviate.py

# ---- Demo retrieve (sin subir imagen, usando un path montado en /app) ----
.PHONY: retrieve
retrieve:
	@echo "Consultando: $(QUERY_IMAGE)"
	$(CURL) -X POST "$(API_URL)/retrieve" \
	 -H "Content-Type: application/json" \
	 -d '{"query_image":"$(QUERY_IMAGE)","top_k":$(TOP_K),"prefer_online":true}' | python -m json.tool

# ---- Limpieza de Docker (por si te quedas sin espacio) ----
.PHONY: clean-docker
clean-docker:
	docker builder prune -af
	docker system prune -af
	@echo "TIP: 'docker volume prune -f' limpia volúmenes no usados (cuidado)."

# ---- Subir un archivo y luego hacer retrieve con el path devuelto ----
# Uso:
#   make upload-retrieve FILE=./data/images/SYNTH/img_0001.jpg TOP_K=8
FILE ?= ./data/images/SYNTH/img_0001.jpg

.PHONY: upload-retrieve
upload-retrieve:
	@test -f "$(FILE)" || (echo "ERROR: no existe el archivo '$(FILE)'" && exit 1)
	@echo "Subiendo archivo: $(FILE)"
	@RESP="$$(curl -s -X POST "$(API_URL)/upload" -H "Expect:" -F "file=@$(FILE)")" ;\
	echo "Respuesta /upload: $$RESP" ;\
	PATH_OUT="$$(echo "$$RESP" | python -c 'import sys, json; d=json.load(sys.stdin); print(d.get("path") or d.get("filepath") or d.get("saved_path") or d.get("url") or "")')" ;\
	if [ -z "$$PATH_OUT" ]; then echo "ERROR: no encontré el campo 'path' en la respuesta del /upload"; exit 1; fi ;\
	echo "Ruta en el servidor: $$PATH_OUT" ;\
	echo "Consultando /retrieve TOP_K=$(TOP_K)..." ;\
	curl -s -X POST "$(API_URL)/retrieve" \
	  -H "Content-Type: application/json" \
	  -d "$$(printf '{\"query_image\":\"%s\",\"top_k\":%s,\"prefer_online\":true}' "$$PATH_OUT" "$(TOP_K)")" \
	| python -m json.tool

.PHONY: fo-app
fo-app:
	docker compose run --rm -p 5151:5151 indexer \
	  fiftyone app launch $(or $(FO_DATASET_NAME),fashion_demo) \
	  --address 0.0.0.0 --port 5151 --remote
