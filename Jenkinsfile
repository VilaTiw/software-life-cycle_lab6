pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Завантаження файлів з репозиторію на GitHub
                git "https://github.com/VilaTiw/software-life-cycle_lab6"
            }
        }

        stage('Test') {
            steps {
                // Імітація запуску тестів
                echo 'Тести виконано!'
            }
        }

        stage('Archive Files') {
            steps {
                // Створення архіву з усіма файлами проекту
                sh 'tar -czvf project_archive.tar.gz .'
            }
        }

        stage('Move to Cargo Folder') {
            steps {
                // Створення папки cargo, якщо її ще немає
                sh 'mkdir -p cargo'

                // Переміщення архіву в папку cargo
                sh 'mv project_archive.tar.gz cargo/'
                echo 'Архів переміщено до папки cargo'
            }
        }
    }
}
