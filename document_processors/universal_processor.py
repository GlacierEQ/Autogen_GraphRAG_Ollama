"""
Universal document processor for GraphRAG integration.
Handles multiple document types and dispatches to specific processors.
"""
import os
import logging
import argparse
import yaml
import shutil
from typing import Dict, List, Optional, Any, Tuple
import concurrent.futures
import time

# Import specific document processors
from word_processor import WordDocumentProcessor
from pdf_processor import PDFDocumentProcessor

logger = logging.getLogger(__name__)

class UniversalDocumentProcessor:
    """Universal document processor for handling multiple document types."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional configuration file path."""
        self.config = self._load_config(config_path)
        self.processors = self._initialize_processors()
        
        # Set up logging
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config.get("log_file", None)
        )
        
        # Configure parallel processing
        self.max_workers = self.config.get("max_workers", 4)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file or use defaults."""
        default_config = {
            "log_level": "INFO",
            "max_workers": 4,
            "processors": {
                "word": {
                    "enabled": True,
                    "chunk_size": 300,
                    "chunk_overlap": 100
                },
                "pdf": {
                    "enabled": True,
                    "ocr_enabled": True,
                    "ocr_language": "eng",
                    "chunk_size": 300,
                    "chunk_overlap": 100,
                    "extract_images": False
                }
            },
            "output_dir": "input/markdown",
            "backup_dir": "input/originals",
            "file_extensions": {
                "word": [".docx", ".doc"],
                "pdf": [".pdf"]
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            return default_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # Merge with defaults to ensure all fields exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config[key], dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return default_config
    
    def _initialize_processors(self) -> Dict[str, Any]:
        """Initialize document processors based on configuration."""
        processors = {}
        
        # Initialize Word processor if enabled
        if self.config["processors"]["word"]["enabled"]:
            processors["word"] = WordDocumentProcessor(self.config["processors"]["word"])
        
        # Initialize PDF processor if enabled
        if self.config["processors"]["pdf"]["enabled"]:
            processors["pdf"] = PDFDocumentProcessor(self.config["processors"]["pdf"])
        
        return processors
    
    def _get_processor_for_file(self, file_path: str) -> Tuple[str, Any]:
        """Determine appropriate processor for a file based on extension."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        for processor_type, extensions in self.config["file_extensions"].items():
            if ext in extensions and processor_type in self.processors:
                return processor_type, self.processors[processor_type]
        
        return None, None
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file with the appropriate processor."""
        result = {
            "file": file_path,
            "success": False,
            "output_path": None,
            "processor_type": None,
            "error": None
        }
        
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            
            # Get appropriate processor
            processor_type, processor = self._get_processor_for_file(file_path)
            result["processor_type"] = processor_type
            
            if processor is None:
                result["error"] = f"No suitable processor found for {file_path}"
                logger.warning(result["error"])
                return result
            
            # Process the file
            start_time = time.time()
            output_path = processor.convert_to_markdown(file_path, output_dir)
            duration = time.time() - start_time
            
            # Check if successful
            if not output_path.startswith("Error"):
                result["success"] = True
                result["output_path"] = output_path
                result["duration"] = duration
                logger.info(f"Successfully processed {file_path} in {duration:.2f}s")
                
                # Backup original file if configured
                if self.config.get("backup_dir"):
                    backup_dir = self.config["backup_dir"]
                    os.makedirs(backup_dir, exist_ok=True)
                    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, backup_path)
                    logger.debug(f"Backed up original file to {backup_path}")
            else:
                result["error"] = output_path
                logger.error(f"Failed to process {file_path}: {output_path}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Exception processing {file_path}: {str(e)}", exc_info=True)
        
        return result
    
    def process_directory(self, input_dir: str) -> List[Dict[str, Any]]:
        """Process all compatible files in a directory."""
        results = []
        files_to_process = []
        
        # Find all compatible files
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                processor_type, _ = self._get_processor_for_file(file_path)
                if processor_type:
                    files_to_process.append(file_path)
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in files_to_process}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Exception processing {file}: {str(e)}", exc_info=True)
                    results.append({
                        "file": file,
                        "success": False,
                        "error": str(e)
                    })
        
        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a report of processing results."""
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        report = []
        report.append("# Document Processing Report")
        report.append(f"\nProcessed {len(results)} files: {len(successful)} successful, {len(failed)} failed\n")
        
        if successful:
            report.append("\n## Successfully Processed Files")
            for idx, result in enumerate(successful):
                duration = result.get("duration", 0)
                report.append(f"{idx+1}. **{os.path.basename(result['file'])}** → {os.path.basename(result['output_path'])} ({result['processor_type']}, {duration:.2f}s)")
        
        if failed:
            report.append("\n## Failed Files")
            for idx, result in enumerate(failed):
                report.append(f"{idx+1}. **{os.path.basename(result['file'])}**: {result.get('error', 'Unknown error')}")
        
        return "\n".join(report)

# Command line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Document Processor for GraphRAG")
    parser.add_argument("--input", "-i", required=True, help="Input directory with documents to process")
    parser.add_argument("--config", "-c", help="Path to configuration YAML file")
    parser.add_argument("--report", "-r", help="Output path for processing report (Markdown format)")
    args = parser.parse_args()
    
    processor = UniversalDocumentProcessor(args.config)
    results = processor.process_directory(args.input)
    
    # Print summary
    successful = len([r for r in results if r.get("success")])
    failed = len([r for r in results if not r.get("success")])
    print(f"Processing complete: {successful} successful, {failed} failed")
    
    # Generate report if requested
    if args.report:
        report_content = processor.generate_report(results)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Report written to {args.report}")
