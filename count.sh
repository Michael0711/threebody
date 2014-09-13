echo 'all' 
grep "trade\[[bl]tc " threebody.log | wc -l
echo '-------------------------'
echo 'ltc' 
grep "trade\[ltc " threebody.log | wc -l
echo '-------------------------'
echo 'btc' 
grep "trade\[btc " threebody.log | wc -l
echo '-------------------------'
echo 'btc okcoin' 
grep "trade\[btc okcoin" threebody.log | wc -l
echo '-------------------------'
echo 'btc tfoll' 
grep "trade\[btc tfoll" threebody.log | wc -l
echo '-------------------------'
echo 'btc huobi' 
grep "trade\[btc huobi" threebody.log | wc -l
echo '-------------------------'
echo 'btc btcchina' 
grep "trade\[btc btcchina" threebody.log | wc -l
echo '-------------------------'
echo 'ltc okcoin' 
grep "trade\[ltc okcoin" threebody.log | wc -l
echo '-------------------------'
echo 'ltc tfoll' 
grep "trade\[ltc tfoll" threebody.log | wc -l
echo '-------------------------'
echo 'ltc huobi' 
grep "trade\[ltc huobi" threebody.log | wc -l
echo '-------------------------'

