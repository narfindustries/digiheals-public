JSON ;ven/gpl - json echo
 ;;0.3;VISTA SYNTHETIC DATA LOADER;;Jul 01, 2019;Build 13
 ;
 ;
 do addService^%webutils("POST","vistaecho","wsPostJSON^JSON")
 q
 ;

wsPostJSON(args,body,result)    ; echo json
 ;
 s U="^"
 ;S DUZ=1
 ;S DUZ("AG")="V"
 ;S DUZ(2)=500
 N USER S USER=$$DUZ^SYNDHP69
 ;
 new err,gr,return ;; creat new variables err,gr
 ; deserialize body into gr
 do decode^%webjson("body","gr","err")
 ; serialize gr into result
 do encode^%webjson("gr","result","err")
 s HTTPRSP("mime")="application/json"
 quit
 ;
