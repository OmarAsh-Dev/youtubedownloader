<?php
// server.php

// Define the path to the Downloads directory
$DOWNLOAD_FOLDER = getenv('USERPROFILE') . '\\Downloads';  // For Windows

if (!file_exists($DOWNLOAD_FOLDER)) {
    mkdir($DOWNLOAD_FOLDER, 0777, true);
}

// Handle the download request
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    header('Content-Type: application/json');
    $data = json_decode(file_get_contents('php://input'), true);
    $url = $data['url'] ?? '';

    if (!$url) {
        echo json_encode(['error' => 'URL must be provided']);
        http_response_code(400);
        exit;
    }

    try {
        require 'vendor/autoload.php'; // Include Composer's autoloader
        $yt = new \pytube\YouTube($url);
        $stream = $yt->streams->filter(['progressive' => true, 'file_extension' => 'mp4'])
            ->orderBy('resolution')
            ->desc()
            ->first();

        if (!$stream) {
            echo json_encode(['error' => 'No suitable stream found.']);
            http_response_code(404);
            exit;
        }

        $file_path = $stream->download($DOWNLOAD_FOLDER);
        echo json_encode(['message' => 'Download completed', 'file' => basename($file_path)]);
    } catch (Exception $e) {
        echo json_encode(['error' => 'Server error: ' . $e->getMessage()]);
        http_response_code(500);
    }

    exit;
}

// Handle static file serving
if (isset($_GET['file'])) {
    $file = basename($_GET['file']);
    $file_path = $DOWNLOAD_FOLDER . DIRECTORY_SEPARATOR . $file;

    if (file_exists($file_path)) {
        header('Content-Disposition: attachment; filename="' . $file . '"');
        header('Content-Type: application/octet-stream');
        header('Content-Length: ' . filesize($file_path));
        readfile($file_path);
        exit;
    } else {
        http_response_code(404);
        echo 'File not found.';
        exit;
    }
}
?>

<!-- Make sure to include a simple HTML interface in the same file or as a separate file. -->
