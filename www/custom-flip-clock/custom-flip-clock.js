/* global customElements*/
/* global HTMLElement*/
customElements.whenDefined('card-tools').then(() => {
    var cardTools = customElements.get('card-tools');
    
    class FlipClockCard extends cardTools.LitElement {
        setConfig(config) {
            this.config = config;
        }
        render() {
            return cardTools.LitHtml
            `
                ${this._renderStyle()}
                ${cardTools.LitHtml `
                    <ha-card>
                        <div class="clock">
                            <div class="digit tenhour">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>

                            <div class="digit hour">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>

                            <div class="digit tenmin">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>

                            <div class="digit min">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>

                            <div class="digit tensec">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>

                            <div class="digit sec">
                                <span class="base"></span>
                                <div class="flap over front"></div>
                                <div class="flap over back"></div>
                                <div class="flap under"></div>
                            </div>
                        </div>
                    </ha-card>
                `}
            `;
        }
        
        _renderStyle() {
            return cardTools.LitHtml `
                <style>
                    $flipColour: #fff;
                    $flipColourDark: darken($flipColour, 35%);
                    $textColour: #333;
                    $textColourDark: darken($textColour, 35%);

                    html {
                        height: 100%;
                    }

                    body {
                        height: 100%;
                        background: #85D8CE;
                        background: linear-gradient(135deg, #085078, #85D8CE);
                    }

                    .digit {
                        position: relative;
                      float: left;
                      width: 10vw;
                      height: 15vw;
                      background-color: $flipColour;
                      border-radius: 1vw;
                        text-align: center;
                      font-family: Oswald, sans-serif;
                      font-size: 11vw;
                    }

                    .base {
                        display: block;
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: $textColour;
                    }

                    .flap {
                        display: none;
                        position: absolute;
                        width: 100%;
                        height: 50%;
                        background-color: $flipColour;
                        left: 0;
                        top: 0;
                        border-radius: 1vw 1vw 0 0;
                        transform-origin: 50% 100%;
                        backface-visibility: hidden;
                        overflow: hidden;

                        &::before {
                            content: attr(data-content);
                            position: absolute;
                            left: 50%;
                        }

                        &.front::before,
                        &.under::before {
                            top: 100%;
                            transform: translate(-50%, -50%);
                        }

                        &.back {
                            transform: rotateY(180deg);
                            &::before {
                                top: 100%;
                                transform:  translate(-50%, -50%) rotateZ(180deg);
                            }
                        }
                    
                        &.over {
                            z-index: 2;
                        }

                        &.under {
                            z-index: 1;
                        }

                        &.front {
                            animation: flip-down-front 300ms ease-in both;
                        }

                        &.back {
                            animation: flip-down-back 300ms ease-in both;
                        }

                        &.under {
                            animation: fade-under 300ms ease-in both;
                        }

                    }

                    @keyframes flip-down-front {
                        0% {
                            transform: rotateX(0deg);
                            background-color: $flipColour;
                            color: $textColour;
                        }
                        100% {
                            transform: rotateX(-180deg);
                            background-color: $flipColourDark;
                            color: $textColourDark;
                        }
                    }

                    @keyframes flip-down-back {
                        0% {
                            transform: rotateY(180deg) rotateX(0deg);
                            background-color: $flipColourDark;
                            color: $textColourDark;
                        }
                        100% {
                            transform: rotateY(180deg) rotateX(180deg);
                            background-color: $flipColour;
                            color: $textColour;
                        }
                    }

                    @keyframes fade-under {
                        0% {
                            background-color: $flipColourDark;
                            color: $textColourDark;
                        }
                        100% {
                            background-color: $flipColour;
                            color: $textColour;
                        }
                    }

                    .clock {
                        position: absolute;
                        width: 70vw;
                        top: 50%;
                        left: 15vw;
                        transform: translateY(-50%);
                        perspective: 100vw;
                        perspective-origin: 50% 50%;

                        .digit {
                            margin-right: 1vw;
                            &:nth-child(2n+2) { margin-right: 3.5vw; }
                            &:last-child { margin-right: 0; }
                        }

                    }  
                    ha-card {
                        padding: 16px;
                    }
                </style>
            `;
        }
        
        set hass(hass) {
            function flipTo(digit, n){
                var current = digit.attr('data-num');
                digit.attr('data-num', n);
                digit.find('.front').attr('data-content', current);
                digit.find('.back, .under').attr('data-content', n);
                digit.find('.flap').css('display', 'block');
                setTimeout(function(){
                    digit.find('.base').text(n);
                    digit.find('.flap').css('display', 'none');
                }, 350);
            }
            
            function jumpTo(digit, n){
                digit.attr('data-num', n);
                digit.find('.base').text(n);
            }
            
            function updateGroup(group, n, flip){
                var digit1 = $('.ten'+group);
                var digit2 = $('.'+group);
                n = String(n);
                if(n.length == 1) n = '0'+n;
                var num1 = n.substr(0, 1);
                var num2 = n.substr(1, 1);
                if(digit1.attr('data-num') != num1){
                    if(flip) flipTo(digit1, num1);
                    else jumpTo(digit1, num1);
                }
                if(digit2.attr('data-num') != num2){
                    if(flip) flipTo(digit2, num2);
                    else jumpTo(digit2, num2);
                }
            }
            
            function setTime(flip){
                var t = new Date();
                updateGroup('hour', t.getHours(), flip);
                updateGroup('min', t.getMinutes(), flip);
                updateGroup('sec', t.getSeconds(), flip);
            }
            
            $(document).ready(function(){
                
                setTime(false);
                setInterval(function(){
                    setTime(true);
                }, 1000);
                
            });
            this.requestUpdate();
        }
    }
    
    customElements.define("flip-clock-card", FlipClockCard);
});

setTimeout(() => {
    if(customElements.get('card-tools')) return;
    customElements.define('flip-clock-card', class extends HTMLElement{
        setConfig() { throw new Error("Can't find card-tools. See https://github.com/thomasloven/lovelace-card-tools");}
        
    });
}, 2000);

