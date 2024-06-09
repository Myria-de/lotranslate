#!/bin/bash
# Bitte URLs und Dateinamen anpassen
# Downloads: https://download.documentfoundation.org/libreoffice/
# Für andere Versionen Versionsnummern, Dateinamen
# und Download-URL anpassen.
LOVERSION="24.2.4"
BASEVERSION="24.2"
DLBASEVERSION="24.2.4"
DLURL="https://download.documentfoundation.org/libreoffice/stable/${DLBASEVERSION}/deb/x86_64/"

## Konfiguration Ende ##
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PARENTDIR="$(dirname "$SCRIPTPATH")"

if [ $UID = "0" ]; then
 echo "Diese Script bitte nicht als root ausführen"
 exit 1
fi

if [ -e $PARENTDIR/libreoffice/program/python ]
 then
  echo "Libre Office ist bereits in $PARENTDIR/libreoffice installiert. Abbruch."
  exit 1
fi

FILEMAIN="LibreOffice_${LOVERSION}_Linux_x86-64_deb"
FILETRANS="LibreOffice_${LOVERSION}_Linux_x86-64_deb_langpack_de"
FILEHELP="LibreOffice_${LOVERSION}_Linux_x86-64_deb_helppack_de"
INSTALLDIR="${SCRIPTPATH}/LO_${LOVERSION}"

if [ ! -d ${INSTALLDIR} ]; then
mkdir ${INSTALLDIR}
fi
cd ${INSTALLDIR}

FILELIST="$FILEMAIN $FILETRANS $FILEHELP"
for i in $FILELIST; do
 if [ ! -f "$i.tar.gz" ]; then
  echo "Download: $i.tar.gz"
  wget $DLURL$i.tar.gz
 fi

 if [ -f "$i.tar.gz" ]; then
  echo "Entpacke: $i.tar.gz"
  mkdir $i
  tar xvf $i.tar.gz -C $i --strip-components 1
else
  echo "Fehler: $i.tar.gz nicht gefunden"
fi

done

if [ ! -d ${INSTALLDIR}/install ]; then
 mkdir ${INSTALLDIR}/install
fi

cd ${INSTALLDIR}/install
echo "Extrahiere deb-Pakete..."
for i in $FILELIST; do
  for j in ../$i/DEBS/*.deb; do dpkg-deb -x $j . ; done
done
echo "Passe bootstraprc an"
cd opt/libreoffice${BASEVERSION}/program
chmod +w bootstraprc
cp bootstraprc bootstraprc.orig
# Portable Installation im Home-Verzeichnis
# Benutzerprofil soll im Installationsordner erstellt werden
sed -i 's/$SYSUSERCONFIG\/libreoffice\/4/$ORIGIN\/../' bootstraprc
# Dateien verschieben
mv $INSTALLDIR/install/opt/libreoffice${BASEVERSION} ${PARENTDIR}
mv ${PARENTDIR}/libreoffice${BASEVERSION} ${PARENTDIR}/libreoffice
#Symlink für .desktop-Datei
cd $PARENTDIR/libreoffice/program
ln -s soffice libreoffice$BASEVERSION
# Desktop-Datei kopieren
cp $SCRIPTPATH/startcenter.desktop ~/Schreibtisch/startcenter.desktop

#Aufräumen
cd $SCRIPTPATH
if [ -d LO_${LOVERSION} ]
then
rm -r LO_${LOVERSION}
fi
echo "Fertig"
