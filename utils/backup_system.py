import os
import shutil
import datetime
import argparse
from pathlib import Path
from config.ai_os_config import get_config_manager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup(backup_dir: str, config_backup: bool = True, data_dirs: Optional[List[str]] = None):
    """Creates a backup of configuration and/or specified data directories."""
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = backup_path / f"backup_{timestamp}"
    current_backup_dir.mkdir(parents=True, exist_ok=True)

    if config_backup:
        logger.info("Creating configuration backup...")
        try:
            config_manager = get_config_manager()
            config_manager.create_backup(str(current_backup_dir / "config_backup.yaml"))
            logger.info(f"Configuration backup created at {current_backup_dir / 'config_backup.yaml'}")
        except Exception as e:
            logger.error(f"Failed to create configuration backup: {e}")

    if data_dirs:
        logger.info("Creating data backup...")
        for data_dir in data_dirs:
            source_path = Path(data_dir)
            if source_path.exists():
                archive_name = current_backup_dir / source_path.name
                try:
                    shutil.make_archive(str(archive_name), 'zip', source_path)
                    logger.info(f"Data backup for {source_path} created at {archive_name}.zip")
                except Exception as e:
                    logger.error(f"Failed to create data backup for {source_path}: {e}")
            else:
                logger.warning(f"Data directory not found: {source_path}")

def restore_backup(backup_file: str, restore_config: bool = True, restore_data: bool = True):
    """Restores from a backup file."""
    backup_file_path = Path(backup_file)
    if not backup_file_path.exists():
        logger.error(f"Backup file not found: {backup_file}")
        return

    if restore_config:
        logger.info("Restoring configuration from backup...")
        try:
            config_manager = get_config_manager()
            config_manager.restore_backup(str(backup_file_path))
            logger.info(f"Configuration restored from {backup_file}")
        except Exception as e:
            logger.error(f"Failed to restore configuration from {backup_file}: {e}")

    if restore_data:
        logger.info("Restoring data from backup...")
        try:
            # Assuming the backup file is a zip archive of data directories
            # This part needs to be more sophisticated if data is backed up differently
            shutil.unpack_archive(str(backup_file_path), extract_dir=backup_file_path.parent)
            logger.info(f"Data restored from {backup_file}")
        except Exception as e:
            logger.error(f"Failed to restore data from {backup_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Automated backup and restore system for AI-OS.")
    parser.add_argument("action", choices=["create", "restore"], help="Action to perform: 'create' or 'restore'.")
    parser.add_argument("--backup_dir", type=str, default="./backups",
                        help="Directory to store/find backups.")
    parser.add_argument("--config", action="store_true", help="Include configuration in backup/restore.")
    parser.add_argument("--data_dirs", nargs='*', help="List of data directories to backup (e.g., 'data' 'logs').")
    parser.add_argument("--backup_file", type=str, help="Path to the backup file for restore action.")

    args = parser.parse_args()

    if args.action == "create":
        create_backup(args.backup_dir, args.config, args.data_dirs)
    elif args.action == "restore":
        if not args.backup_file:
            logger.error("Backup file must be specified for restore action.")
            return
        restore_backup(args.backup_file, args.config, True) # Assuming data restore is always true for now

if __name__ == "__main__":
    main()