#/bin/bash
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN="\033[0;36m"
L_BLUE='\033[1;34m'  # Light Blue
NC='\033[0m'  # No Color

MAIN_SCRIPT="punch.py"
MAIN_CONFIG="config.yaml"
EXAMPLE_CONFIG="example.yaml"

# prepare env dir
mkdir auto-punch
HOME_DIR="$PWD/auto-punch"
cd $HOME_DIR


highlight_printf_n () {
  printf "${YELLOW}$1${NC}\n"
}


install_chrome () {
  TARGET_CHROME_VERSION="latest"
  # TARGET_CHROME_VERSION="99.0.4844.51"
  
  highlight_printf_n "Installing [chrome.rpm] .. \n"
  CHROME_VERSION=$(rpm -qa |grep google-chrome-stable |cut -d '-'  -f 4)
  if [[ -z $CHROME_VERSION ]]; then
    yum install -y https://dl.google.com/linux/chrome/rpm/stable/x86_64/google-chrome-stable-${TARGET_CHROME_VERSION}-1.x86_64.rpm
    CHROME_VERSION=$(rpm -qa |grep google-chrome-stable |cut -d '-'  -f 4)
    [[ -z $CHROME_VERSION ]] && echo "[x] [google-chrome-stable] not found in [rpm -qa]; exit 1 " && exit 1
  fi
}


install_chrome_driver () {
  cd "/opt"
  highlight_printf_n "Installing [unzip] .. \n"
  yum -y -q install unzip
  highlight_printf_n "Downloading [chrome driver] under [/opt] .. \n"
  
  CHROME_DRIVER_URL="https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip"
  wget -q --spider $CHROME_DRIVER_URL
  [[ $? != "0" ]] && echo "[x] [$CHROME_DRIVER_URL] not working in; exit 1 " && exit 1
  wget $CHROME_DRIVER_URL
  unzip "chromedriver_linux64.zip"
  cd $HOME_DIR
}


yum_install_packages () {
  highlight_printf_n "Going to install a bunch of packages, may take a while.. \n"
  highlight_printf_n "(0/3) ... \n"
  yum -y -q install make gcc gcc-c++
  highlight_printf_n "(1/3) ... \n"
  yum -y -q group install "Development Tools"
  highlight_printf_n "(2/3) ... \n"
  yum -y -q install zlib-devel  readline* libffi-devel openssl-devel tk-devel sqlite-devel
  highlight_printf_n "(3/3) ... \n"
}


install_python_37 () {
  if [[ ! -f /usr/local/bin/python3 ]]; then
    highlight_printf_n "Downloading [python37] .. \n"
    wget "https://www.python.org/ftp/python/3.7.12/Python-3.7.12.tgz"
    tar zxf "Python-3.7.12.tgz"
    cd ./Python-3.7.12
    highlight_printf_n "Going to compile [python37], may take a while .. \n" && sleep 1
    highlight_printf_n "Configuring .. \n" && sleep 1
    ./configure > /dev/null
    echo
    highlight_printf_n "Make .. \n" && sleep 1
    make > /dev/null
    echo
    highlight_printf_n "Make Install .. \n" && sleep 1
    make install > /dev/null
    cd $HOME_DIR
    sleep 1
  fi
}


pip3_install_packages () {
  highlight_printf_n "Install python modules by pip3 .. \n"
  PIP3_PATH="/usr/local/bin/pip3"
  [[ -z $(which $PIP3_PATH) ]] && echo "[x] [$PIP3_PATH] not found; exit 1 " && exit 1
  /usr/local/bin/pip3 install selenium > /dev/null
  /usr/local/bin/pip3 install requests > /dev/null
  /usr/local/bin/pip3 install PyYaml > /dev/null
}


clean_files () {
  cd $HOME_DIR
  mkdir -p ./archived
  [[ -f "Python-3.7.12.tgz" ]] && mv "Python-3.7.12.tgz" ./archived
  [[ -f "google-chrome-stable_current_x86_64.rpm" ]] && mv "google-chrome-stable_current_x86_64.rpm" ./archived

  [[ -f ../$MAIN_SCRIPT ]] && mv ../$MAIN_SCRIPT ./
  [[ -f ../$MAIN_CONFIG ]] && mv ../$MAIN_CONFIG ./
  [[ -f ../$EXAMPLE_CONFIG ]] && mv ../$EXAMPLE_CONFIG ./
  [[ -f ../README.md ]] && mv ../README.md ./

  [[ ! -f $MAIN_CONFIG ]] && cp ./$EXAMPLE_CONFIG ./$MAIN_CONFIG

  chmod a+x ./$MAIN_SCRIPT
  highlight_printf_n "Change owner to [$SUDO_USER] for all subpathes under [$HOME_DIR]"
  chown -R $SUDO_USER:$SUDO_USER $HOME_DIR

  # danger zone
  rm -f "/opt/chromedriver_linux64.zip"
}


final_hints () {
  echo
  echo "+---------------------------+"
  echo "|         READ ME           |"
  echo "+---------------------------+"
  echo
  printf "${L_BLUE}* Further Steps:  check - README.md${NC}\n"
  printf "  1. Update [${YELLOW}<email address>${NC}] in [${GREEN}$MAIN_CONFIG${NC}]\n"
  printf "  2. Go [${YELLOW}https://api.slack.com/]${NC} to register webhook to send DM to your channel\n"
  printf "  3. Go ${CYAN}Google${NC} [${YELLOW}my user agent${NC}] and paste result into [${GREEN}$MAIN_CONFIG${NC}] \n"
  printf "  4. Go Paste [${YELLOW}<YOUR PASSWORD>${NC}] and check [global.system.hrm-url] in [${GREEN}$MAIN_CONFIG${NC}] \n"
  printf "  5. Test Script in by command [${YELLOW}/usr/local/bin/python3 $HOME_DIR/$MAIN_SCRIPT -f $HOME_DIR/$MAIN_CONFIG] ${NC}\n"
  printf "  6. Setup crontab [${YELLOW}crontab -e${NC}] e.g.\n"
  printf "      ${YELLOW} 55 8 * * 1-5 /usr/local/bin/python3 $HOME_DIR/$MAIN_SCRIPT -f $HOME_DIR/$MAIN_CONFIG  ${NC} \n"
  printf "      ${YELLOW} 50 17 * * 1-5 /usr/local/bin/python3 $HOME_DIR/$MAIN_SCRIPT -f $HOME_DIR/$MAIN_CONFIG ${NC} \n"
  echo
  echo
  printf "${L_BLUE}* Note: ${NC} \n"
  highlight_printf_n "  1. Do not run punch.py or set crontab as root user."
  highlight_printf_n "  2. Alway test yourself before crontab execute the script."

}



# main
install_chrome
install_chrome_driver
yum_install_packages
install_python_37
pip3_install_packages
clean_files
final_hints
