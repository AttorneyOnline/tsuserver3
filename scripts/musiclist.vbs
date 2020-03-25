' this script will create a looping musiclist for you from any folder containing mp3 and opus files
' ogg is not natively supported by windows media player and ogg files renamed to mp3 will lag the script
On Error Resume Next
Set objFS = CreateObject("Scripting.FileSystemObject")
Set objPlayer = createobject("wmplayer.ocx.7")
Set objStdOut = WScript.StdOut
inFolder="E:\Attorney Online\Attorney Online supermerge webAO edition\base\sounds\music" 'music folder here
outFile="E:\Git\tsuserver3\config\music.yaml" 'musiclist here
Set objFile = objFS.CreateTextFile(outFile,True)
Set objFolder = objFS.GetFolder(inFolder)
objFile.Write "- category: == Songs ==" & vbCrLf
objFile.Write "  songs:"
For Each strFile In objFolder.Files
	If objFS.GetExtensionName(strFile) = "mp3" Or objFS.GetExtensionName(strFile) = "opus" Then ' Or objFS.GetExtensionName(strFile) = "ogg" Then
        strFileName = strFile.Path
        objFile.Write vbCrLf
        objStdOut.Write objFS.GetFileName(strFileName) & vbCrLf
		objFile.Write "  - name: " & chr(34) & objFS.GetFileName(strFileName) & chr(34) & vbCrLf
        objFile.Write "    length: "
        objFile.Write CInt(objPlayer.mediaCollection.add(strFileName).duration)
	End If	
Next 
objPlayer.close
objFile.Close