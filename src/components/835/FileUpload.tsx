import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface FileUploadProps {
  onFileUploaded: (fileInfo: any) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('token');
      const response = await fetch('/api/parser/upload-835', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus({
          type: 'success',
          message: `File "${file.name}" uploaded successfully! Processing...`
        });
        onFileUploaded(result);
      } else {
        setUploadStatus({
          type: 'error',
          message: result.detail || 'Upload failed. Please try again.'
        });
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: 'Network error. Please check your connection and try again.'
      });
    } finally {
      setUploading(false);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt', '.edi', '.835']
    },
    maxFiles: 1,
    disabled: uploading
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragActive && !isDragReject 
            ? 'border-blue-400 bg-blue-50' 
            : isDragReject 
              ? 'border-red-400 bg-red-50'
              : uploading 
                ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
                : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600">Uploading remittance file...</p>
            </>
          ) : (
            <>
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive 
                    ? isDragReject 
                      ? 'Invalid file type' 
                      : 'Drop the 835 file here'
                    : 'Upload 835 Remittance File'
                  }
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Drag and drop your .txt, .edi, or .835 file here, or click to browse
                </p>
              </div>
            </>
          )}
        </div>

        {/* File Format Info */}
        <div className="mt-6 p-4 bg-gray-100 rounded-lg text-left">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Supported Formats:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li className="flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              835 EDI Remittance Advice (.txt, .edi, .835)
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              X12 5010 format supported
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              Multiple claims per file
            </li>
          </ul>
        </div>
      </div>

      {/* Status Messages */}
      {uploadStatus.type && (
        <div className={`
          mt-6 p-4 rounded-lg flex items-center
          ${uploadStatus.type === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
          }
        `}>
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
          ) : (
            <XCircle className="w-5 h-5 text-red-500 mr-3" />
          )}
          <div>
            <p className={`text-sm font-medium ${
              uploadStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
            }`}>
              {uploadStatus.message}
            </p>
          </div>
        </div>
      )}

      {/* Upload Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <AlertTriangle className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-900">Tips for Best Results:</h4>
            <ul className="mt-2 text-sm text-blue-800 space-y-1">
              <li>• Ensure file contains valid ISA header segments</li>
              <li>• File should start with "ISA*" and end with "IEA*"</li>
              <li>• Both professional (837P) and institutional (837I) claims supported</li>
              <li>• AI explanations available for all CARC/RARC adjustment codes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;