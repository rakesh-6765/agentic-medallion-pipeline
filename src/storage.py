"""Explicit Parquet (local) and managed Delta (Databricks) snapshot stores."""

import json
from pathlib import Path
from typing import Protocol

from pyspark.sql import DataFrame, SparkSession

from medallion.config import identifier


class Store(Protocol):
    def write(self, layer: str, name: str, frame: DataFrame) -> DataFrame: ...

    def read(self, layer: str, name: str) -> DataFrame: ...

    def manifest(self, document: dict) -> None: ...


class LocalStore:
    def __init__(self, spark: SparkSession, root: Path):
        self.spark = spark
        self.root = root.resolve()
        marker = self.root / ".medallion-output"
        if self.root.exists() and any(self.root.iterdir()) and not marker.is_file():
            raise ValueError(f"Refusing to overwrite unowned output directory: {self.root}")
        self.root.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=True)

    def _path(self, layer: str, name: str) -> str:
        return str(self.root / identifier(layer) / identifier(name))

    def write(self, layer: str, name: str, frame: DataFrame) -> DataFrame:
        frame.write.mode("overwrite").parquet(self._path(layer, name))
        return self.read(layer, name)

    def read(self, layer: str, name: str) -> DataFrame:
        return self.spark.read.parquet(self._path(layer, name))

    def manifest(self, document: dict) -> None:
        target = self.root / "run_manifest.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
        temporary.replace(target)


class CatalogStore:
    def __init__(self, spark: SparkSession, *, catalog: str, prefix: str = "medallion"):
        self.spark = spark
        self.catalog = identifier(catalog)
        self.prefix = identifier(prefix)
        for layer in ("bronze", "silver", "gold"):
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.schema(layer)}")

    def schema(self, layer: str) -> str:
        return f"`{self.catalog}`.`{self.prefix}_{identifier(layer)}`"

    def table(self, layer: str, name: str) -> str:
        return f"{self.schema(layer)}.`{identifier(name)}`"

    def write(self, layer: str, name: str, frame: DataFrame) -> DataFrame:
        frame.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(self.table(layer, name))
        return self.read(layer, name)

    def read(self, layer: str, name: str) -> DataFrame:
        return self.spark.table(self.table(layer, name))

    def manifest(self, document: dict) -> None:
        frame = self.spark.createDataFrame(
            [(document["run_id"], document["status"], json.dumps(document, sort_keys=True))],
            "run_id string, status string, manifest_json string",
        )
        self.write("silver", "run_manifest", frame)
