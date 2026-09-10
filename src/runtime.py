"""Local Spark bootstrap; Databricks uses its supplied Spark session instead."""

import os
import sys
from pathlib import Path


def _java_home(home: Path) -> Path:
    return home / "Contents" / "Home" if (home / "Contents" / "Home").is_dir() else home


def install_local_java() -> Path:
    """Explicitly download a full JDK into this Python environment, not globally."""
    import jdk

    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Activate a virtual environment before installing managed Java")
    marker = Path(sys.prefix) / "medallion-java-home.txt"
    if marker.exists():
        home = _java_home(Path(marker.read_text().strip()))
        if (home / "bin" / "java").is_file():
            marker.write_text(str(home) + "\n")
            return home
    home = _java_home(Path(jdk.install("21", path=str(Path(sys.prefix) / "medallion-jdk"))))
    marker.write_text(str(home) + "\n")
    return home


def local_spark(app_name: str = "medallion-pipeline"):
    from pyspark.sql import SparkSession

    marker = Path(sys.prefix) / "medallion-java-home.txt"
    if marker.exists():
        home = _java_home(Path(marker.read_text().strip()))
        if not (home / "bin" / "java").is_file():
            raise RuntimeError("Managed Java is missing; run 'medallion setup-java'")
        os.environ["JAVA_HOME"] = str(home)
    elif not os.environ.get("JAVA_HOME"):
        raise RuntimeError("Run 'medallion setup-java' or set JAVA_HOME to a full JDK 17/21")
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    spark = (
        SparkSession.builder.master("local[2]")
        .appName(app_name)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.ansi.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark
