 pipeline {
        agent {
        label 'rdjenkins'
        }
        stages {
            stage('install requirements') {
                steps {
                    
                    withPythonEnv('python3'){
    sh 'ls'
}
                }
            }
            stage('run test') {
                steps {
                    
                    withPythonEnv('python3'){

                        sh '/apps/dakota/bin/dakota -i params.in ' 


                    }
                }
            }



        }
      post {
 
              success {


           archiveArtifacts artifacts: '*.dat', fingerprint: true

                }


    
 
        

    
    }
    }