((LitElement) => {
	const html = LitElement.prototype.html;
	const css = LitElement.prototype.css;

	class CustomMultilineTextInput extends LitElement {

		static get properties() {
			return {
				_hass: {},
				_config: {},
				stateObj: {},
				state: {}
			}
		}

		static get styles() {
			return css`
				.flex {
					display: flex;
					align-items: center;
					justify-content: space-evenly;
				}
				.button {
					cursor: pointer;
					padding: 16px;
				}
				.textarea {
					background: inherit;
					border: inherit;
					border-left: 1px solid var(--primary-color);
					border-bottom: 1px solid var(--primary-color);
					box-shadow: none;
					color: inherit; /*var(--primary-color)*/;
					font: inherit;
					font-size: 16px;
					height: auto;
					letter-spacing: inherit;
					line-height: inherit;
					margin-top: 20px;
					outline: none;
					padding-left: 5px;
					padding-bottom: 5px;
					min-height: 80px;
					overflow-y: auto;
					word-wrap: break-word;
					width: 100%;
					word-spacing: inherit;
					resize: none;
				}
				.text-bold {
					font-weight: bold;
				}
				.text-italic {
					font-style: italic; 
				}
				.text-left {
					float: left;
				}
				.text-red {
					box-shadow: 0 0 3px 6px rgba(255, 0, 0, 0.3);
					border-color: #dc3545;
					transition: border-color .15s ease-in-out,box-shadow .15s ease-in-out;
				}
				.text-right {
					float: right;
				}
				.text-small {
					font-size: 11px;
				}
				.hidden {
					display: none;
				}
				.button-disabled {
					cursor: auto;
					pointer-events: none;
				}
			`;
		}

		updated() {
			let _this = this;
			this.updateComplete.then(() => {
				let new_state = _this.getState();
				// only overwrite if state has changed since last overwrite
				if(_this.state.last_updated_text === null || new_state !== _this.state.last_updated_text) {
					_this.setText(new_state, true);
				}
			});
		}

		render() {
			return html`
				<ha-card .hass="${this._hass}" .config="${this._config}" class="background">
					${this.state.title ? html`<div class="card-header">${this.state.title}</div>` : null}
					<div class="card-content">
						<textarea maxlength="${this.state.max_length !== -1 ? this.state.max_length : ""}" @keyup="${() => this.onKeyupTextarea()}" class="textarea text-red" id="mainBox" placeholder="${this.state.placeholder_text}">${this.getState()}</textarea>
					</div>
					${this.state.showButtons ? html`
						<div class="flex">
							${Object.keys(this.state.buttons).map(this.renderButton.bind(this))}
						</div>` : null}
				</ha-card>`;
		}

		getCardSize() {
			return Math.round(this.scrollHeight / 50);
		}

		renderButton(key) {
			return this.state.buttons[key]
				? html`<div class="button" title="${this.state.hints[key]}" id="button-${key}" @tap="${() => { if(this.callAction(key) !== false) { this.callService(key); }}}"><ha-icon icon="${this.state.icons[key]}"></ha-icon></div>`
				: null;
		}

		getState() {
			const value = this.stateObj ? this.stateObj.state : this.state.default_text;
			return value.replace("\\n", "\n");
		}

		getText() {
			return this.shadowRoot.querySelector(".textarea").value;
		}

		setText(val, entity_update) {
			if(entity_update === true) {
				this.state.last_updated_text = val;
			}
			this.shadowRoot.querySelector(".textarea").value = val;
			this.updateCharactersInfoText();
		}

		clearText() {
			clearTimeout(this.state.autosave_timeout);
			this.setText('');
		}

		pasteText() {
			clearTimeout(this.state.autosave_timeout);
			let elem = _this.shadowRoot.querySelector(".textarea")
			if ("iPhone" in navigator.platform) {
				this.pasteTextIphone(elem);
			}
			else {
				let _this = this;
				if(elem) {
					elem.focus();
					let val = elem.value;
					if(typeof navigator.clipboard.readText === "function") {
						navigator.clipboard.readText().then((text) => {
							_this.setText(val + text);
							_this.onKeyupTextarea();
						}, (err) => { console.error("Error on paste: ", err); });
					}
					else {
						console.warn("Sorry, your browser does not support the clipboard paste function.");
					}
				}
			}
		}

		pasteTextIphone(el){
			var oldContentEditable = el.contentEditable,
			oldReadOnly = el.readOnly,
			range = document.createRange();
	
			el.contentEditable = true;
			el.readOnly = false;
			range.selectNodeContents(el);
			
			var s = window.getSelection();
			s.removeAllRanges();
			s.addRange(range);
			
			el.contentEditable = oldContentEditable;
			el.readOnly = oldReadOnly;
			
			document.execCommand('paste');
		}

		copyText() {
			clearTimeout(this.state.autosave_timeout);
			let elem = this.shadowRoot.querySelector(".textarea");
			if ("iPhone" in navigator.platform) {
				this.copyTextIphone(elem);
			}
			else {
				if(elem) {
					elem.focus();
					let val = elem.value;
					if(typeof navigator.clipboard.writeText === "function") {
						if(val !== null && val !== ''){
							navigator.clipboard.writeText(val);
						}
					}
					else {
						console.warn("Sorry, your browser does not support the clipboard copy function.");
					}
				}
			}
		}

		copyTextIphone(el){
			var oldContentEditable = el.contentEditable,
			oldReadOnly = el.readOnly,
			range = document.createRange();
	
			el.contentEditable = true;
			el.readOnly = false;
			range.selectNodeContents(el);
			
			var s = window.getSelection();
			s.removeAllRanges();
			s.addRange(range);
			
			el.setSelectionRange(0, 999999); // A big number, to cover anything that could be inside the element.
			
			el.contentEditable = oldContentEditable;
			el.readOnly = oldReadOnly;
			
			document.execCommand('copy');
		}

		onKeyupTextarea() {
			if(this.state.autosave) {
				clearTimeout(this.state.autosave_timeout);
				let _this = this;
				this.state.autosave_timeout = setTimeout(function() {
					if(_this.callAction('save') !== false) {
						_this.callService('save');
					}
				}, 1000);
			}
			this.updateCharactersInfoText();
		}

		updateCharactersInfoText() {
			let textLength = this.shadowRoot.querySelector(".textarea").value.length;
			let button_save = this.shadowRoot.querySelector("#button-save");
			let disable_button = false;

			if(this.state.max_length !== false) {
				let mainBoxAreaElem = this.shadowRoot.querySelector("#mainBox")

				if(textLength >= this.state.max_length) {
					mainBoxAreaElem.classList.add("text-red");
					disable_button = true;
				}
				else {
					mainBoxAreaElem.classList.remove("text-red");
				}
				if(textLength <= this.state.max_length) {
					disable_button = false;
				}
			}

			if(button_save) {
				if(disable_button) {
					button_save.classList.add("button-disabled");
					button_save.classList.add("text-red");
				}
				else {
					button_save.classList.remove("button-disabled");
					button_save.classList.remove("text-red");
				}
			}
		}

		callAction(action) {
			if (typeof this.state.actions[action] === 'function') {
				return this.state.actions[action]();
			}
		}

		callService(service) {
			if(this.state.entity_type === 'input_text' || this.state.entity_type === 'var') {
				let value = (typeof this.state.service_values[service] === 'function' ? this.state.service_values[service]() : this.state.service_values[service]);
				if(this.state.service[service]) {
					this._hass.callService(this.state.entity_type, this.state.service[service], {entity_id: this.stateObj.entity_id, value: value});
				}
			}
		}

		actionSave() {
			let len = this.getText().length;
			let length_check = len >= this.state.min_length && (this.state.max_length === false || len <= this.state.max_length);
			return length_check;
		}

		actionClear() {
			this.clearText();
			if(this.state.save_on_clear && this.callAction('save') !== false) {
				this.callService('save');
			}
		}

		actionPaste() {
			this.pasteText();
		}

		actionCopy() {
			this.copyText();
		}

		setConfig(config) {
			const supported_entity_types = [
				'input_text',
				'var', 		// custom component: https://community.home-assistant.io/t/custom-component-generic-variable-entities/128627
			];

			const actions = {
				save: () => { return this.actionSave(); },
				paste: () => { return this.actionPaste(); },
				clear: () => { return this.actionClear(); },
				copy: () => { return this.actionCopy(); },
			};

			// paste has no service, clear must be "confirmed" by saving
			const services = {
				'input_text': {
					save: 'set_value',
				},
				'var': {
					save: 'set',
				},
			};

			const service_values = {
				save: () => { return this.getText(); },
				paste: null,
				clear: '',
				copy: null
			};

			const buttons = {
				save: true,
				paste: true,
				clear: true,
				copy: true,
			};

			const icons = {
				save: 'mdi:content-save-outline',
				paste: 'mdi:content-paste',
				clear: 'mdi:trash-can-outline',
				copy: 'mdi:content-copy',
			};

			const hints = {
				save: 'Save',
				paste: 'Paste from clipboard',
				clear: 'Clear text',
				copy: 'Copy text to clipboard'
			};

			let entity_type = config.entity.split('.')[0];
			if (!config.entity || !supported_entity_types.includes(entity_type)) {
				throw new Error('Please define an entity of type: ' + supported_entity_types.join(', '));
			}

			this.state = {
				autosave: config.autosave === true,
				entity: config.entity,
				max_length: parseInt(config.max_length) || false,
				min_length: parseInt(config.min_length) || 0,
				placeholder_text: config.placeholder_text || "",
				save_on_clear: config.save_on_clear === true,
				title: config.title,

				autosave_timeout: null,
				default_text: "",
				entity_type: entity_type,
				last_updated_text: null,
				showButtons: config.buttons !== false,

				actions: Object.assign({}, actions),
				buttons: Object.assign({}, buttons, config.buttons),
				hints: Object.assign({}, hints),
				icons: Object.assign({}, icons, config.icons),
				service: Object.assign({}, services[entity_type]),
				service_values: Object.assign({}, service_values),
			};

			this.state.min_length = Math.max(this.state.min_length, 0);

			if(this.state.max_length !== false && this.state.max_length <= 0) {
				throw new Error("The max length should be greater than zero.");
			}
			if(this.state.min_length > this.state.max_length && this.state.max_length !== false) {
				throw new Error("The min length must not be greater than max length.");
			}

			this._config = config;
		}

		set hass(hass) {
			this._hass = hass;

			if(hass && this._config) {
				this.stateObj = this._config.entity in hass.states ? hass.states[this._config.entity] : null;
				if(this.stateObj) {
					if(this.state.title === undefined) {
						this.state.title = this.stateObj.attributes.friendly_name || "";
					}
					if(this.state.entity_type === "input_text") {
						if(this.stateObj.attributes.mode !== "text") {
							throw new Error("An input_text entity must be in 'text' mode!");
						}

						if(this.state.min_length === 0 && (this.stateObj.attributes.min || 0) > 0) {
							this.state.min_length = this.stateObj.attributes.min;
							console.warn("Entity " + this._config.entity + " requires at least " + this.stateObj.attributes.min + " characters.");
						}
						if(this.state.max_length === false || this.stateObj.attributes.max < this.state.max_length) {
							if(this.state.max_length !== false) {
								console.warn("Entity " + this._config.entity + " allows less characters (" + this.stateObj.attributes.max + ") than desired.");
							}
							this.state.max_length = this.stateObj.attributes.max;
						}
					}
				}
			}
		}
	}

	customElements.define('custom-multiline-text-input-card', CustomMultilineTextInput);
})(window.LitElement || Object.getPrototypeOf(customElements.get("hui-view")));
