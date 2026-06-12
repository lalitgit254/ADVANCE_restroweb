import cloudinary
import cloudinary.uploader
from flask import current_app


class CloudinaryService:
    @staticmethod
    def configure():
        cloudinary.config(
            cloud_name=current_app.config.get('CLOUDINARY_CLOUD_NAME'),
            api_key=current_app.config.get('CLOUDINARY_API_KEY'),
            api_secret=current_app.config.get('CLOUDINARY_API_SECRET'),
        )

    @staticmethod
    def upload_image(file, folder='restaurant'):
        if not current_app.config.get('CLOUDINARY_CLOUD_NAME'):
            return CloudinaryService._local_fallback(file, folder)

        CloudinaryService.configure()
        try:
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                transformation=[
                    {'quality': 'auto', 'fetch_format': 'auto'},
                    {'width': 800, 'crop': 'limit'},
                ],
            )
            return result['secure_url']
        except Exception as e:
            current_app.logger.error('Cloudinary upload failed: %s', str(e))
            return CloudinaryService._local_fallback(file, folder)

    @staticmethod
    def _local_fallback(file, folder):
        import os
        from werkzeug.utils import secure_filename
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        return f'/uploads/{folder}/{filename}'

    @staticmethod
    def delete_image(public_id):
        if not current_app.config.get('CLOUDINARY_CLOUD_NAME'):
            return
        CloudinaryService.configure()
        try:
            cloudinary.uploader.destroy(public_id)
        except Exception:
            pass
