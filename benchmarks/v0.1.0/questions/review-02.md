次のReactコードをレビューしてください。
useEffect(() => { fetch('/api?q=' + query).then(r => r.json()).then(setItems); }, []);
queryはpropsの文字列です。重大度・根拠・修正案を提示してください。
